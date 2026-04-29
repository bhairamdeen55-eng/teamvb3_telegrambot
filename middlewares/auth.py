# middlewares/auth.py
from typing import Callable, Dict, Any, Awaitable, Optional
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from db.database import async_session_factory
from db.crud import UserCRUD

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
