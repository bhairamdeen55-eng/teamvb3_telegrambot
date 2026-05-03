# handlers/callbacks.py
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from loguru import logger
from utils.keyboards import main_menu_kb, back_kb, subject_selection_keyboard

callback_router = Router()

@callback_router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery) -> None:
    await callback.answer()

@callback_router.callback_query(F.data.startswith("page_"))
async def pagination_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    parts = callback.data.split("_")
    if len(parts) >= 3:
        page = int(parts[2]) if parts[2].isdigit() else 0
        await callback.message.edit_text(f"Page {page + 1}")

@callback_router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery, bot: Bot) -> None:
    await callback.answer()  # तुरंत बटन बंद
    user = callback.from_user
    chats_to_check = [
        ("@theteamvb", "📢 Channel"),
        ("@teamvb2", "👥 Group"),
    ]
    not_joined = []
    for chat_id, chat_type in chats_to_check:
        try:
            member = await bot.get_chat_member(chat_id=chat_id, user_id=user.id)
            if member.status in ["left", "kicked"]:
                not_joined.append((chat_id, chat_type))
        except:
            not_joined.append((chat_id, chat_type))

    if not_joined:
        text = "❌ *Abhi bhi join nahi kiye:*\n\n"
        for chat_id, chat_type in not_joined:
            text += f"➡️ {chat_type}: {chat_id}\n"
        text += "\nPehle join karein, phir dubara check karein!"
        keyboard_buttons = []
        for chat_id, chat_type in not_joined:
            url = chat_id.replace("@", "https://t.me/")
            keyboard_buttons.append([
                InlineKeyboardButton(text=f"Join {chat_type}", url=url)
            ])
        keyboard_buttons.append([
            InlineKeyboardButton(text="🔄 Check Again", callback_data="check_subscription")
        ])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await callback.message.edit_text(
            "✅ *Aap dono mein hai!* Bot istemal kar sakte hain.\n\n/start",
            parse_mode="Markdown"
        )

# ========== MAIN MENU ==========

@callback_router.callback_query(F.data == "menu_quiz")
async def menu_quiz_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text(
        "📝 <b>Smart Quiz Mode</b>\n\n"
        "Select a topic or try a random quiz!",
        reply_markup=subject_selection_keyboard()
    )

@callback_router.callback_query(F.data == "menu_dpp")
async def menu_dpp_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text(
        "📚 <b>Daily Practice Problems</b>\n\n"
        "Select a topic to get problems.",
        reply_markup=subject_selection_keyboard()
    )

@callback_router.callback_query(F.data == "menu_photo")
async def menu_photo_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text(
        "📸 <b>Photo Test</b>\n\n"
        "Upload a photo of your handwritten answer for AI evaluation.\n\n"
        "Simply send a photo here!",
        reply_markup=back_kb("menu")
    )

@callback_router.callback_query(F.data == "menu_scores")
async def menu_scores_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text(
        "📊 <b>My Scores</b>\n\nFeature coming soon...",
        reply_markup=back_kb("menu")
    )

@callback_router.callback_query(F.data == "menu_leaderboard")
async def menu_leaderboard_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text(
        "🏆 <b>Leaderboard</b>\n\nFeature coming soon...",
        reply_markup=back_kb("menu")
    )

@callback_router.callback_query(F.data == "menu_premium")
async def menu_premium_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text(
        "⭐ <b>Premium Subscription</b>\n\n"
        "Unlock all premium features:\n"
        "- Unlimited quizzes\n"
        "- Detailed analytics\n"
        "- Priority AI processing\n\n"
        "Contact admin for subscription.",
        reply_markup=back_kb("menu")
    )

@callback_router.callback_query(F.data == "menu_help")
async def menu_help_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text(
        "❓ <b>Help</b>\n\n"
        "Use /menu to see all features.\n"
        "Use /quiz for topic-wise quizzes.\n"
        "Use /dpp for Daily Practice Problems.\n"
        "Upload handwritten answers for AI evaluation.\n\n"
        "For any issues, contact @theteamvb.",
        reply_markup=back_kb("menu")
    )

@callback_router.callback_query(F.data == "menu")
async def back_to_main_menu(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text(
        "📌 <b>Main Menu</b>",
        reply_markup=main_menu_kb()
    )

# ========== TOPIC / SUBJECT SELECTION ==========

@callback_router.callback_query(F.data.startswith("quiz_topic_"))
async def quiz_topic_handler(callback: CallbackQuery):
    await callback.answer()
    topic = callback.data.replace("quiz_topic_", "")
    text = f"✅ You selected *{topic}* for Quiz.\n\n🔄 Loading your quiz... (feature coming soon)"
    await callback.message.edit_text(text, reply_markup=back_kb("menu"))

@callback_router.callback_query(F.data.startswith("dpp_topic_"))
async def dpp_topic_handler(callback: CallbackQuery):
    await callback.answer()
    topic = callback.data.replace("dpp_topic_", "")
    text = f"✅ You selected *{topic}* for DPP.\n\n🔄 Loading practice problems... (feature coming soon)"
    await callback.message.edit_text(text, reply_markup=back_kb("menu"))

@callback_router.callback_query(F.data.startswith("subject:"))
async def subject_handler(callback: CallbackQuery):
    await callback.answer()
    subject = callback.data.split(":")[1]
    text = f"✅ You selected *{subject}*.\n\nThis feature is under development."
    await callback.message.edit_text(text, reply_markup=back_kb("menu"))

@callback_router.callback_query(F.data == "gk")
async def gk_callback_handler(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("🌍 GK section coming soon!", reply_markup=back_kb("menu"))

@callback_router.callback_query(F.data == "random")
async def random_callback_handler(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("🎲 Random quiz starting soon!", reply_markup=back_kb("menu"))

@callback_router.callback_query(F.data == "back")
async def back_callback_handler(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("🔙 Returning to menu...", reply_markup=main_menu_kb())
