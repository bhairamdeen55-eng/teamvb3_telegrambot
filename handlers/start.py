# handlers/start.py
from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from loguru import logger
from utils.texts import START_TEXT, HELP_TEXT
from utils.keyboards import main_menu_kb
from config import settings
from db.database import async_session_factory
from db.models import SharedTest
from sqlalchemy import select
from datetime import datetime
from utils.helpers import start_shared_test_sessions

start_router = Router()

@start_router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext, command, user=None, session=None):
    await state.clear()
    args = command.args
    if args and args.startswith("test_"):
        code = args[5:]
        async with async_session_factory() as session:
            result = await session.execute(select(SharedTest).where(SharedTest.code == code))
            shared_test = result.scalar_one_or_none()
            if not shared_test:
                await message.answer("❌ यह टेस्ट कोड मान्य नहीं है।")
                return
            if shared_test.expires_at < datetime.utcnow():
                await message.answer("⏰ यह टेस्ट लिंक expired हो गया है।")
                return
            await start_shared_test_sessions(
                user_id=message.from_user.id,
                message=message,
                state=state,
                questions=shared_test.questions
            )
            logger.info(f"User {message.from_user.id} started shared test {code}")
            return
    # सामान्य /start
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
