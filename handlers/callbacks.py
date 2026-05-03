# handlers/callbacks.py (Debug version)
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from loguru import logger

callback_router = Router()

@callback_router.callback_query()
async def debug_callback(callback: CallbackQuery, bot: Bot):
    """हर callback को पकड़ेगा और data दिखाएगा"""
    data = callback.data
    logger.info(f"Callback received: {data} from user {callback.from_user.id}")
    await callback.answer(f"Clicked: {data}", show_alert=True)
    # Optionally, edit message to show what was clicked
    await callback.message.edit_text(f"🔍 Debug: you clicked `{data}`")
