# handlers/callbacks.py
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, FSInputFile
from loguru import logger
from config import settings
from pathlib import Path

callback_router = Router()

async def send_help_response(message):
    """QR कोड इमेज और पूरा हेल्प टेक्स्ट भेजने का फ़ंक्शन"""
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

    # पहले इमेज (बहुत छोटे caption के साथ)
    image_path = settings.ASSETS_DIR / "help_qr.jpg"
    if image_path.exists():
        photo = FSInputFile(str(image_path))
        await message.answer_photo(photo=photo, caption="📌 TeamVB Help & Support")
    else:
        await message.answer("📌 TeamVB Help & Support")

    # फिर पूरा हेल्प टेक्स्ट
    await message.answer(help_text)

@callback_router.callback_query(F.data == "menu_help")
async def menu_help_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    await send_help_response(callback.message)

@callback_router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery) -> None:
    await callback.answer()

@callback_router.callback_query()
async def universal_callback_handler(callback: CallbackQuery, bot: Bot) -> None:
    await callback.answer()
    logger.info(f"Callback received: {callback.data} from user {callback.from_user.id}")
    await callback.message.edit_text(f"✅ आपने दबाया: `{callback.data}`")
