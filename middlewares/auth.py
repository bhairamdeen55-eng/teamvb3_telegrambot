# middlewares/auth.py
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
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

        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
            username = event.from_user.username
            first_name = event.from_user.first_name
            last_name = event.from_user.last_name
            data["event_type"] = "message"
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id
            username = event.from_user.username
            first_name = event.from_user.first_name
            last_name = event.from_user.last_name
            data["event_type"] = "callback"

        if not user_id:
            return await handler(event, data)

        # ✅ async with use karo — session poore handler lifecycle mein open rahega
        async with async_session_factory() as session:
            try:
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
                data["db_user"] = user
                data["session"] = session

                return await handler(event, data)

            except Exception as e:
                logger.error(f"AuthMiddleware error for user {user_id}: {e}", exc_info=True)
                data["user"] = None
                data["db_user"] = None
                data["session"] = None
                return await handler(event, data)
                
