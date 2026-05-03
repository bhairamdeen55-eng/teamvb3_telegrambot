# middlewares/auth.py
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
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

        if user_id and async_session_factory:
            # ✅ FIX: session manually open karo taaki handler ke andar bhi open rahe
            session = async_session_factory()
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
                data["session"] = session  # ✅ session ab handler complete hone tak open rahega

                return await handler(event, data)

            except Exception as e:
                logger.error(f"AuthMiddleware error for user {user_id}: {e}", exc_info=True)
                data["user"] = None
                data["db_user"] = None
                data["session"] = None
                return await handler(event, data)

            finally:
                # ✅ Handler complete hone ke BAAD session close hoga
                await session.close()

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

        # Subscription check callback block mat karo
        if isinstance(event, CallbackQuery) and event.data == "check_subscription":
            return await handler(event, data)

        # Saare required chats check karo
        not_joined = []
        for chat_id, chat_type, chat_url in self.REQUIRED_CHATS:
            try:
                member = await bot.get_chat_member(chat_id=chat_id, user_id=user.id)
                if member.status in ["left", "kicked"]:
                    not_joined.append((chat_id, chat_type, chat_url))
            except Exception as e:
                logger.warning(f"Could not check {chat_id} for user {user.id}: {e}")
                # ✅ Warning pe block mat karo — gracefully pass karo
                # not_joined mein mat daalo agar sirf check fail hua

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
                logger.error(f"Could not send subscription message to {user.id}: {e}")

            return  # Handler block karo

        return await handler(event, data)
        
