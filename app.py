import os
from dotenv import load_dotenv

load_dotenv()

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN
from db.database import init_db
from handlers.start import start
from handlers.menu import menu
from handlers.quiz import quiz_command, handle_quiz_text
from handlers.dpp import dpp_command, handle_dpp_text
from handlers.photo_test import photo_command, handle_photo_upload
from handlers.callbacks import handle_callbacks
from handlers.admin import (
    set_channel,
    set_channel_id,
    set_gate,
    set_ai_provider,
    settings_cmd,
    stats_cmd,
)
from utils.logger import setup_logger


async def route_text(update, context):
    if await handle_quiz_text(update, context):
        return
    if await handle_dpp_text(update, context):
        return

    await update.message.reply_text(
        "Main menu ke liye /menu use karo."
    )


async def route_photo(update, context):
    if await handle_photo_upload(update, context):
        return

    await update.message.reply_text(
        "Photo test start karne ke liye /photo use karo."
    )


async def error_handler(update, context):
    setup_logger().exception("Unhandled error: %s", context.error)


def main():
    logger = setup_logger()
    init_db()

    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN missing in environment")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("quiz", quiz_command))
    app.add_handler(CommandHandler("dpp", dpp_command))
    app.add_handler(CommandHandler("photo", photo_command))

    app.add_handler(CommandHandler("setchannel", set_channel))
    app.add_handler(CommandHandler("setchannelid", set_channel_id))
    app.add_handler(CommandHandler("setgate", set_gate))
    app.add_handler(CommandHandler("setai", set_ai_provider))
    app.add_handler(CommandHandler("settings", settings_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))

    app.add_handler(CallbackQueryHandler(handle_callbacks))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, route_text))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, route_photo))

    app.add_error_handler(error_handler)

    logger.info("teamvb3 bot started")
    app.run_polling(close_loop=False)


if __name__ == "__main__":
    main()
