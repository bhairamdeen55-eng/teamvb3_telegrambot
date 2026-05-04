# handlers/start.py
from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile
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
from pathlib import Path

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
    help_text = (
        "📚 <b>HELP MENU – TEAMVB BOT 📚</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "/start → Yah command bot ko start karne ke liye hai isse bot start hota .\n"
        "👉 Isse tum bot ka use shuru karte ho.\n\n"
        "/quiz → Quiz start karta hai jisme tum questions attempt kar sakte ho.\n"
        "👉 Practice + test dono ke liye useful hai.\n\n"
        "/dpp → Daily Practice Problems deta hai.\n"
        "👉 Roz ke questions se consistency improve hoti hai.\n\n"
        "/leaderboard → Top students ki ranking dikhata hai.\n"
        "👉 Tum apni performance compare kar sakte ho dusron se.\n\n"
        "/help → Yeh help menu open karta hai.\n"
        "👉 Sabhi commands aur unka use samjhata hai.\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "📢 <b>IMPORTANT INSTRUCTIONS</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "✔ Bot use karne se pehle required channels join karo\n"
        "✔ “Try Again” button press karo agar access na mile\n"
        "✔ Sirf study related use karein\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "🚀 <b>TEAMVB FEATURES</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ AI Based Quiz System\n"
        "✅ Daily Practice (DPP)\n"
        "✅ Fast Result & Analysis\n"
        "✅ Competitive Leaderboard\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "🎯 <b>STUDY HARD • STAY CONSISTENT • CRACK JEE 🎯</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "🔥 <b>TEAMVB — JEE & BOARD ASPIRANTS 🔥</b>"
    )
    
    # QR कोड इमेज का path (आपने assets में help_qr.jpg रखा है)
    image_path = settings.ASSETS_DIR / "help_qr.jpg"
    
    if image_path.exists():
        photo = FSInputFile(str(image_path))
        await message.answer_photo(
            photo=photo,
            caption=help_text
        )
    else:
        # इमेज नहीं मिली तो केवल टेक्स्ट भेजें
        await message.answer(help_text)

@start_router.message(Command("menu"))
async def menu_handler(message: Message) -> None:
    await message.answer("📌 <b>Main Menu</b>", reply_markup=main_menu_kb())
