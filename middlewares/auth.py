# middlewares/auth.py
import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from db.database import AsyncSessionLocal
from db.crud import get_or_create_user

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseMiddleware):
    """Har update pe user DB mein register karo aur ban check karo."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # User object lo
        tg_user = data.get("event_from_user")
        if not tg_user:
            return await handler(event, data)

        try:
            async with AsyncSessionLocal() as session:
                # User get ya create karo
                user = await get_or_create_user(
                    session=session,
                    telegram_id=tg_user.id,
                    full_name=tg_user.full_name,
                    username=tg_user.username,
                )

                # Ban check
                if user.is_banned:
                    if isinstance(event, Message):
                        await event.answer("🚫 Tumhara account ban kar diya gaya hai.")
                    elif isinstance(event, CallbackQuery):
                        await event.answer("🚫 Account banned!", show_alert=True)
                    return

                # Session aur user data inject karo
                data["db_user"] = user
                data["session"] = session

                return await handler(event, data)

        except Exception as e:
            logger.error(f"AuthMiddleware error for user {tg_user.id}: {e}")
            # Session error pe bhi handler chalne do — graceful degradation
            data["db_user"] = None
            data["session"] = None
            return await handler(event, data)
            
