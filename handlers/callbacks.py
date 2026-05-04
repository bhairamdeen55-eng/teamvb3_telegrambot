# handlers/callbacks.py
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, FSInputFile
from loguru import logger
from config import settings
from pathlib import Path

callback_router = Router()

async def send_help(message):
    help_text = (
        "📚 <b>HELP MENU – TEAMVB BOT 📚</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "/start → Bot ko start karta hai\n"
        "/quiz → Quiz start karta hai\n"
        "/dpp → Daily Practice Problems deta hai\n"
        "/help → Help menu dikhata hai\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "📢 <b>IMPORTANT</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "✔ Required channels join karo\n"
        "✔ Study related use karein\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "🚀 <b>TEAMVB FEATURES</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "✅ AI Based Quiz System\n"
        "✅ Daily Practice (DPP)\n"
        "✅ Fast Result & Analysis\n"
        "✅ Competitive Leaderboard\n\n"
        "🔥 <b>TEAMVB — JEE & BOARD ASPIRANTS 🔥</b>"
    )

    image_path = settings.ASSETS_DIR / "help_qr.jpg"
    if image_path.exists():
        photo = FSInputFile(str(image_path))
        await message.answer_photo(photo=photo, caption="📌 TeamVB Help & Support")
    else:
        await message.answer("📌 TeamVB Help & Support")

    await message.answer(help_text)

# "Help & Support" बटन
@callback_router.callback_query(F.data == "menu_help")
async def menu_help_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    await send_help(callback.message)

# "Back" बटन (वापस मेन्यू पर)
@callback_router.callback_query(F.data == "menu")
async def back_to_menu_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    from utils.keyboards import main_menu_kb
    await callback.message.edit_text("📌 <b>Main Menu</b>", reply_markup=main_menu_kb())

# "Quiz" बटन
@callback_router.callback_query(F.data == "menu_quiz")
async def menu_quiz_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    from utils.keyboards import subject_selection_keyboard
    await callback.message.edit_text("📝 <b>Quiz Mode</b>\n\nSelect a topic:", reply_markup=subject_selection_keyboard())

# "DPP" बटन
@callback_router.callback_query(F.data == "menu_dpp")
async def menu_dpp_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    from utils.keyboards import subject_selection_keyboard
    await callback.message.edit_text("📚 <b>Daily Practice Problems</b>\n\nSelect a topic:", reply_markup=subject_selection_keyboard())

# "Photo Test" बटन
@callback_router.callback_query(F.data == "menu_photo")
async def menu_photo_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text("📸 <b>Photo Test</b>\n\nUpload a photo of your question to start AI evaluation.")

# बाकी बटन
@callback_router.callback_query()
async def fallback_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(f"✅ Feature coming soon!")
