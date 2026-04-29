# handlers/start.py
from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from loguru import logger
from utils.texts import START_TEXT, HELP_TEXT
from utils.keyboards import main_menu_kb, remove_kb
from config import settings
from db.crud import UserCRUD

start_router = Router()

@start_router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext, user=None, session=None) -> None:
    await state.clear()
    await message.answer(
        f"👋 Hello {message.from_user.first_name}!\n\n{START_TEXT}",
        reply_markup=main_menu_kb(),
    )
    logger.info("User started bot: {} ({})", message.from_user.id, message.from_user.first_name)

@start_router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(HELP_TEXT)

@start_router.message(Command("menu"))
async def menu_handler(message: Message) -> None:
    await message.answer("📌 <b>Main Menu</b>", reply_markup=main_menu_kb())
