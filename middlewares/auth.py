# middlewares/auth.py
from typing import Callable, Dict, Any, Awaitable, Optional
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from db.database import async_session_factory
from db.crud import UserCRUD


# ========== AUTH MIDDLEWARE ==========

class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id = None
        username = None
        first_name = None
        last_name = None
        
        if isinstance(event, Message):
            if event.from_user:
                user_id = event.from_user.id
                username = event.from_user.username
                first_name = event.from_user.first_name
                last_name = event.from_user.last_name
                data["event_type"] = "message"
        elif isinstance(event, CallbackQuery):
            if event.from_user:
                user_id = event.from_user.id
                username = event.from_user.username
                first_name = event.from_user.first_name
                last_name = event.from_user.last_name
                data["event_type"] = "callback"
        
        if user_id and async_session_factory:
            async with async_session_factory() as session:
                user = await UserCRUD.get_or_create(
                    session,
                    user_id=user_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                )
                if user.is_blocked:
                    if isinstance(event, Message):
                        await event.answer("⛔ Your account has been blocked. Contact admin.")
                    elif isinstance(event, CallbackQuery):
                        await event.answer("⛔ Account blocked", show_alert=True)
                    return
                data["user"] = user
                data["session"] = session
                data["db_user"] = user
                return await handler(event, data)
        
        return await handler(event, data)


# ========== SUBSCRIPTION MIDDLEWARE ==========

class SubscriptionMiddleware(BaseMiddleware):
    """
    Middleware to check if user has joined required channel and group.
    Blocks all access until user joins both.
    """
    
    REQUIRED_CHATS = [
        ("@theteamvb", "📢 Channel", "https://t.me/theteamvb"),
        ("@teamvb2", "👥 Group", "https://t.me/teamvb2"),
    ]

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)
        
        bot = data["bot"]
        
        # Don't block subscription check callbacks
        if hasattr(event, "data") and event.data == "check_subscription":
            return await handler(event, data)
        
        # Check all required chats
        not_joined = []
        for chat_id, chat_type, chat_url in self.REQUIRED_CHATS:
            try:
                member = await bot.get_chat_member(chat_id=chat_id, user_id=user.id)
                if member.status in ["left", "kicked"]:
                    not_joined.append((chat_id, chat_type, chat_url))
            except Exception as e:
                logger.warning(f"Could not check {chat_id} for user {user.id}: {e}")
                not_joined.append((chat_id, chat_type, chat_url))
        
        if not_joined:
            text = "❌ *Bot Use Karne Ke Liye Join Karein*\n\n"
            text += "Aapne niche diye gaye channel aur group join nahi kiye hai:\n\n"
            
            keyboard_buttons = []
            for chat_id, chat_type, chat_url in not_joined:
                text += f"➡️ {chat_type}: {chat_id}\n"
                keyboard_buttons.append([
                    InlineKeyboardButton(text=f"Join {chat_type}", url=chat_url)
                ])
            
            text += "\n✅ Dono join karne ke baad neeche *'Check Karao'* button dabayein!"
            
            keyboard_buttons.append([
                InlineKeyboardButton(text="✅ Check Karao", callback_data="check_subscription")
            ])
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
            
            try:
                await bot.send_message(
                    chat_id=user.id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Could not send subscription message to user {user.id}: {e}")
            
            return  # Block the handler
        
        return await handler(event, data)
