import asyncio
import sys
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import BotCommand, BotCommandScopeDefault, TelegramObject, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from loguru import logger
import aiocron

from config import settings
from loader import bot, dp, storage
from db.database import init_db, close_db
from utils.logger import setup_logging
from handlers.start import start_router
from handlers.menu import menu_router
from handlers.quiz import quiz_router
from handlers.dpp import dpp_router
from handlers.photo_test import photo_test_router
from handlers.callbacks import callback_router
from handlers.admin import admin_router
from middlewares.throttling import ThrottlingMiddleware
from middlewares.auth import AuthMiddleware
from services.test_service import send_daily_tests


# ========== SUBSCRIPTION MIDDLEWARE ==========

class SubscriptionMiddleware(BaseMiddleware):
    # Channel/Group IDs config se le rahe hain, nahi to default
    def __init__(self):
        channel_id = getattr(settings, 'CHANNEL_ID', None) or "@theteamvb"
        group_id = getattr(settings, 'GROUP_ID', None) or "@teamvb2"
        self.REQUIRED_CHATS = [
            (channel_id, "📢 Channel", f"https://t.me/{channel_id.replace('@', '')}"),
            (group_id, "👥 Group", f"https://t.me/{group_id.replace('@', '')}"),
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

        bot_instance = data["bot"]

        # Subscription check callback block mat karo
        if hasattr(event, "data") and event.data == "check_subscription":
            return await handler(event, data)

        # Saare required chats check karo
        not_joined = []
        for chat_id, chat_type, chat_url in self.REQUIRED_CHATS:
            try:
                member = await bot_instance.get_chat_member(chat_id=chat_id, user_id=user.id)
                if member.status in ["left", "kicked"]:
                    not_joined.append((chat_id, chat_type, chat_url))
            except Exception as e:
                logger.warning(f"Could not check {chat_id} for user {user.id}: {e}")

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
                await bot_instance.send_message(
                    chat_id=user.id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Could not send subscription message to {user.id}: {e}")

            return  # Handler block karo

        return await handler(event, data)


# ========== DAILY TEST SCHEDULER (app.py ke andar hi) ==========

@aiocron.crontab("0 8 * * *")  # Har din subah 8:00 UTC (Indian time 1:30 PM)
async def daily_test_job():
    """Sabhi active users ko 5 daily tests bhejein."""
    try:
        logger.info("Running daily test job...")
        await send_daily_tests(bot)
        logger.info("Daily tests sent successfully")
    except Exception as e:
        logger.error(f"Error in daily test job: {e}")


# ========== COMMANDS & STARTUP ==========

async def set_commands() -> None:
    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="menu", description="Main menu"),
        BotCommand(command="quiz", description="Start a quiz"),
        BotCommand(command="dpp", description="Daily practice problems"),
        BotCommand(command="test", description="Upload photo for evaluation"),
        BotCommand(command="score", description="Check your scores"),
        BotCommand(command="help", description="Get help"),
        BotCommand(command="admin", description="Admin panel (admins only)"),
    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())

async def on_startup() -> None:
    logger.info("Starting bot...")
    await init_db()
    await set_commands()

    if settings.SENTRY_DSN:
        import sentry_sdk
        sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=0.1)
        logger.info("Sentry initialized")
    logger.info("Bot started successfully")

async def on_shutdown() -> None:
    logger.info("Shutting down bot...")
    await close_db()
    await bot.session.close()
    await storage.close()
    logger.info("Bot shutdown complete")

def register_routers() -> None:
    dp.include_router(start_router)
    dp.include_router(menu_router)
    dp.include_router(callback_router)
    dp.include_router(quiz_router)
    dp.include_router(dpp_router)
    dp.include_router(photo_test_router)
    dp.include_router(admin_router)
    logger.info("All routers registered")

def register_middlewares() -> None:
    dp.update.outer_middleware(AuthMiddleware())
    dp.update.outer_middleware(SubscriptionMiddleware())
    dp.update.middleware(ThrottlingMiddleware(
        rate=settings.THROTTLE_RATE,
        burst=settings.THROTTLE_BURST
    ))
    logger.info("Middlewares registered: Auth, Subscription, Throttling")


# ========== MAIN ==========

async def main_polling() -> None:
    register_middlewares()
    register_routers()
    await on_startup()
    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        )
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        await on_shutdown()

async def main_webhook() -> None:
    register_middlewares()
    register_routers()
    await on_startup()

    # Webhook URL determine karo (Railway ya manual)
    webhook_url = settings.WEBHOOK_URL
    if not webhook_url and getattr(settings, 'RAILWAY_PUBLIC_DOMAIN', None):
        webhook_url = f"https://{settings.RAILWAY_PUBLIC_DOMAIN}/webhook"

    if webhook_url:
        await bot.set_webhook(
            url=webhook_url,
            secret_token=settings.webhook_secret_value,
            drop_pending_updates=True
        )
        logger.info("Webhook set to {}", webhook_url)
    else:
        logger.warning("No webhook URL configured – bot won't receive updates in webhook mode!")

    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", settings.WEBHOOK_PORT)
    await site.start()
    logger.info("Webhook server started on port {}", settings.WEBHOOK_PORT)
    await asyncio.Event().wait()


if __name__ == "__main__":
    setup_logging()
    try:
        if settings.is_webhook_mode:
            asyncio.run(main_webhook())
        else:
            asyncio.run(main_polling())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user")
        sys.exit(0)
