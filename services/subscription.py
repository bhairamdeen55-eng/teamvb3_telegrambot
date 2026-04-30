# services/subscription.py
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from loguru import logger
from db.models import User, Subscription, SubscriptionTier
from db.crud import UserCRUD
from config import settings

class SubscriptionService:
    TIER_PRICES = {
        SubscriptionTier.MONTHLY: {"price": 99, "days": 30},
        SubscriptionTier.QUARTERLY: {"price": 249, "days": 90},
        SubscriptionTier.YEARLY: {"price": 799, "days": 365},
    }
    
    @staticmethod
    async def check_subscription(session: AsyncSession, user_id: int) -> dict:
        user = await UserCRUD.get(session, user_id)
        if not user:
            return {"active": False, "tier": "free", "expiry": None}
        
        if user.subscription_expiry and user.subscription_expiry > datetime.utcnow():
            return {
                "active": True,
                "tier": user.subscription_tier.value if user.subscription_tier else "free",
                "expiry": user.subscription_expiry,
                "days_left": (user.subscription_expiry - datetime.utcnow()).days,
            }
        
        return {"active": False, "tier": "free", "expiry": None}
    
    @staticmethod
    async def activate_subscription(
        session: AsyncSession,
        user_id: int,
        tier: SubscriptionTier,
        payment_id: Optional[str] = None,
        amount: Optional[float] = None,
    ) -> Optional[Subscription]:
        if tier not in SubscriptionService.TIER_PRICES:
            logger.error("Invalid tier: {}", tier)
            return None
        
        tier_info = SubscriptionService.TIER_PRICES[tier]
        return await UserCRUD.update_subscription(
            session, user_id, tier, tier_info["days"]
        )
    
    @staticmethod
    async def expire_subscriptions(session: AsyncSession) -> int:
        """Expire all subscriptions past their end date"""
        result = await session.execute(
            select(Subscription).where(
                and_(
                    Subscription.is_active == True,
                    Subscription.end_date <= datetime.utcnow(),
                )
            )
        )
        expired = list(result.scalars().all())
        
        for sub in expired:
            sub.is_active = False
            user = await UserCRUD.get(session, sub.user_id)
            if user:
                user.subscription_tier = SubscriptionTier.FREE
                user.subscription_expiry = None
        
        await session.commit()
        if expired:
            logger.info("Expired {} subscriptions", len(expired))
        return len(expired)
    
    @staticmethod
    async def get_subscription_stats(session: AsyncSession) -> dict:
        """Get subscription statistics for admin"""
        total_users = await UserCRUD.get_user_count(session)
        
        result = await session.execute(
            select(User.subscription_tier, func.count(User.id))
            .group_by(User.subscription_tier)
        )
        tier_counts = dict(result.all())
        
        active_subs = await session.execute(
            select(func.count(Subscription.id))
            .where(Subscription.is_active == True)
        )
        
        return {
            "total_users": total_users,
            "tier_breakdown": {k.value if hasattr(k, 'value') else k: v for k, v in tier_counts.items()},
            "active_subscriptions": active_subs.scalar() or 0,
        }
