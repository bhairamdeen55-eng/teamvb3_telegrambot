# db/crud.py
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from db.models import User, Subscription, Quiz, Question, QuizAttempt, DPP, PhotoTest, UserRole, SubscriptionTier

class UserCRUD:
    @staticmethod
    async def get(session: AsyncSession, user_id: int) -> Optional[User]:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_or_create(session: AsyncSession, user_id: int, **kwargs) -> User:
        user = await UserCRUD.get(session, user_id)
        if not user:
            user = User(id=user_id, **kwargs)
            session.add(user)
            await session.commit()
            logger.info("New user created: {}", user_id)
        return user
    
    @staticmethod
    async def update(session: AsyncSession, user_id: int, **kwargs) -> Optional[User]:
        user = await UserCRUD.get(session, user_id)
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            user.updated_at = datetime.utcnow()
            await session.commit()
        return user
    
    @staticmethod
    async def update_subscription(session: AsyncSession, user_id: int, tier: SubscriptionTier, days: int) -> Optional[Subscription]:
        user = await UserCRUD.get(session, user_id)
        if not user:
            return None
        expiry = datetime.utcnow() + timedelta(days=days)
        sub = Subscription(user_id=user_id, tier=tier, end_date=expiry)
        user.subscription_tier = tier
        user.subscription_expiry = expiry
        session.add(sub)
        await session.commit()
        logger.info("Subscription updated: user={} tier={} days={}", user_id, tier.value, days)
        return sub
    
    @staticmethod
    async def check_daily_limit(session: AsyncSession, user_id: int, limit: int = 10) -> bool:
        user = await UserCRUD.get(session, user_id)
        if not user:
            return True
        if user.last_quiz_date and user.last_quiz_date.date() == datetime.utcnow().date():
            return user.daily_quiz_count < limit
        return True
    
    @staticmethod
    async def increment_daily_quiz(session: AsyncSession, user_id: int) -> None:
        user = await UserCRUD.get(session, user_id)
        if not user:
            return
        now = datetime.utcnow()
        if user.last_quiz_date and user.last_quiz_date.date() == now.date():
            user.daily_quiz_count += 1
        else:
            user.daily_quiz_count = 1
            user.last_quiz_date = now
        user.total_quizzes += 1
        await session.commit()
    
    @staticmethod
    async def get_all_users(session: AsyncSession, skip: int = 0, limit: int = 100) -> list[User]:
        result = await session.execute(select(User).offset(skip).limit(limit))
        return list(result.scalars().all())
    
    @staticmethod
    async def get_user_count(session: AsyncSession) -> int:
        result = await session.execute(select(func.count(User.id)))
        return result.scalar()

class QuizCRUD:
    @staticmethod
    async def create(session: AsyncSession, **kwargs) -> Quiz:
        quiz = Quiz(**kwargs)
        session.add(quiz)
        await session.commit()
        await session.refresh(quiz)
        return quiz
    
    @staticmethod
    async def get(session: AsyncSession, quiz_id: int) -> Optional[Quiz]:
        result = await session.execute(select(Quiz).where(Quiz.id == quiz_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_random(session: AsyncSession, topic: Optional[str] = None, limit: int = 1) -> list[Quiz]:
        query = select(Quiz).where(Quiz.is_active == True)
        if topic:
            query = query.where(Quiz.topic == topic)
        query = query.order_by(func.random()).limit(limit)
        result = await session.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_by_topic(session: AsyncSession, topic: str) -> list[Quiz]:
        result = await session.execute(
            select(Quiz).where(Quiz.is_active == True, Quiz.topic == topic)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_active_quizzes(session: AsyncSession) -> list[Quiz]:
        result = await session.execute(select(Quiz).where(Quiz.is_active == True))
        return list(result.scalars().all())

class QuestionCRUD:
    @staticmethod
    async def bulk_create(session: AsyncSession, quiz_id: int, questions: list[dict]) -> list[Question]:
        objs = [Question(quiz_id=quiz_id, **q) for q in questions]
        session.add_all(objs)
        await session.commit()
        for obj in objs:
            await session.refresh(obj)
        return objs
    
    @staticmethod
    async def get_by_quiz(session: AsyncSession, quiz_id: int) -> list[Question]:
        result = await session.execute(
            select(Question).where(Question.quiz_id == quiz_id).order_by(Question.order)
        )
        return list(result.scalars().all())

class AttemptCRUD:
    @staticmethod
    async def create(session: AsyncSession, **kwargs) -> QuizAttempt:
        attempt = QuizAttempt(**kwargs)
        session.add(attempt)
        await session.commit()
        await session.refresh(attempt)
        return attempt
    
    @staticmethod
    async def get_by_user(session: AsyncSession, user_id: int, limit: int = 20) -> list[QuizAttempt]:
        result = await session.execute(
            select(QuizAttempt)
            .where(QuizAttempt.user_id == user_id)
            .order_by(QuizAttempt.completed_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_user_stats(session: AsyncSession, user_id: int) -> dict:
        result = await session.execute(
            select(
                func.count(QuizAttempt.id),
                func.avg(QuizAttempt.percentage),
                func.sum(QuizAttempt.correct_count),
                func.sum(QuizAttempt.wrong_count),
            ).where(QuizAttempt.user_id == user_id, QuizAttempt.completed == True)
        )
        row = result.one()
        return {
            "total_attempts": row[0] or 0,
            "avg_percentage": round(row[1] or 0, 2),
            "total_correct": row[2] or 0,
            "total_wrong": row[3] or 0,
        }

class DPPCRUD:
    @staticmethod
    async def create(session: AsyncSession, **kwargs) -> DPP:
        dpp = DPP(**kwargs)
        session.add(dpp)
        await session.commit()
        await session.refresh(dpp)
        return dpp
    
    @staticmethod
    async def get(session: AsyncSession, dpp_id: int) -> Optional[DPP]:
        result = await session.execute(select(DPP).where(DPP.id == dpp_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_topic(session: AsyncSession, topic: str) -> list[DPP]:
        result = await session.execute(
            select(DPP).where(DPP.is_active == True, DPP.topic == topic)
        )
        return list(result.scalars().all())

class PhotoTestCRUD:
    @staticmethod
    async def create(session: AsyncSession, **kwargs) -> PhotoTest:
        pt = PhotoTest(**kwargs)
        session.add(pt)
        await session.commit()
        await session.refresh(pt)
        return pt
    
    @staticmethod
    async def get_by_user(session: AsyncSession, user_id: int, limit: int = 10) -> list[PhotoTest]:
        result = await session.execute(
            select(PhotoTest)
            .where(PhotoTest.user_id == user_id)
            .order_by(PhotoTest.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
