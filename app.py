# app.py
import asyncio
import sys
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from loguru import logger

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
    dp.update.middleware(ThrottlingMiddleware(rate=settings.THROTTLE_RATE, burst=settings.THROTTLE_BURST))
    logger.info("Middlewares registered: Auth, Throttling")

async def main_polling() -> None:
    register_middlewares()
    register_routers()
    await on_startup()
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        await on_shutdown()

async def main_webhook() -> None:
    register_middlewares()
    register_routers()
    await on_startup()
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
