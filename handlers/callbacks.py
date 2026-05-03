# handlers/callbacks.py
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from loguru import logger

callback_router = Router()

# यह हैंडलर **हर** callback को पकड़ेगा और तुरंत जवाब देगा
@callback_router.callback_query()
async def universal_callback_handler(callback: CallbackQuery, bot: Bot) -> None:
    await callback.answer()  # सबसे पहले घड़ी बंद करें
    logger.info(f"Callback received: {callback.data} from user {callback.from_user.id}")
    await callback.message.edit_text(f"✅ आपने दबाया: `{callback.data}`")
