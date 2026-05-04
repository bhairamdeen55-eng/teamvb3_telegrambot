from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from loguru import logger
from handlers.start import send_help  # वही फ़ंक्शन इस्तेमाल करें

callback_router = Router()

@callback_router.callback_query(F.data == "menu_help")
async def menu_help_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    await send_help(callback.message)

@callback_router.callback_query()
async def universal_callback_handler(callback: CallbackQuery, bot: Bot) -> None:
    await callback.answer()
    logger.info(f"Callback received: {callback.data} from user {callback.from_user.id}")
    await callback.message.edit_text(f"✅ आपने दबाया: `{callback.data}`")
