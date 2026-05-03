from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from loguru import logger

callback_router = Router()

@callback_router.callback_query()
async def universal_callback_handler(callback: CallbackQuery, bot: Bot) -> None:
    await callback.answer()
    logger.info(f"Callback received: {callback.data} from user {callback.from_user.id}")
    await callback.message.edit_text(f"✅ आपने दबाया: `{callback.data}`")
