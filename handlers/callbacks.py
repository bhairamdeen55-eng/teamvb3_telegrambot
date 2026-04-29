# handlers/callbacks.py
from aiogram import Router, F
from aiogram.types import CallbackQuery
from loguru import logger

callback_router = Router()

@callback_router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery) -> None:
    """No-operation callback — for disabled buttons"""
    await callback.answer()

@callback_router.callback_query(F.data.startswith("page_"))
async def pagination_callback(callback: CallbackQuery) -> None:
    """Generic pagination handler — route to specific handlers"""
    data = callback.data
    parts = data.split("_")
    if len(parts) >= 3:
        action = parts[1]
        page = int(parts[2]) if parts[2].isdigit() else 0
        await callback.answer(f"Page {page + 1}")
    else:
        await callback.answer()
