# handlers/callbacks.py
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from loguru import logger
from utils.keyboards import main_menu_kb, subject_selection_keyboard, back_kb

callback_router = Router()

# ========== NO-OP & PAGINATION ==========

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

# ========== SUBSCRIPTION CHECK CALLBACK ==========

@callback_router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery, bot: Bot) -> None:
    """Callback for 'Check Karao' button after joining channels"""
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

# ========== MAIN MENU CALLBACKS ==========

@callback_router.callback_query(F.data == "menu_quiz")
async def menu_quiz_handler(callback: CallbackQuery) -> None:
    """जब यूज़र मेन्यू से 'Quiz' चुनता है"""
    await callback.message.edit_text(
        "📝 <b>Quiz</b>\n\nChoose a topic to start your quiz:",
        reply_markup=subject_selection_keyboard()
    )
    await callback.answer()

@callback_router.callback_query(F.data == "menu_dpp")
async def menu_dpp_handler(callback: CallbackQuery) -> None:
    """जब यूज़र मेन्यू से 'DPP' चुनता है"""
    await callback.message.edit_text(
        "📚 <b>Daily Practice Problems</b>\n\nChoose a topic to view problems:",
        reply_markup=subject_selection_keyboard()
    )
    await callback.answer()

@callback_router.callback_query(F.data == "menu_photo")
async def menu_photo_handler(callback: CallbackQuery) -> None:
    """जब यूज़र मेन्यू से 'Photo Test' चुनता है"""
    await callback.message.edit_text(
        "📸 <b>Photo Test</b>\n\n"
        "Upload a photo of your handwritten answer, and AI will evaluate it.\n\n"
        "Simply send a photo here!",
        reply_markup=back_kb("menu")
    )
    await callback.answer()

@callback_router.callback_query(F.data == "menu_scores")
async def menu_scores_handler(callback: CallbackQuery) -> None:
    """जब यूज़र मेन्यू से 'My Scores' चुनता है"""
    await callback.message.edit_text(
        "📊 <b>My Scores</b>\n\nFeature coming soon...",
        reply_markup=back_kb("menu")
    )
    await callback.answer()

@callback_router.callback_query(F.data == "menu_leaderboard")
async def menu_leaderboard_handler(callback: CallbackQuery) -> None:
    """जब यूज़र मेन्यू से 'Leaderboard' चुनता है"""
    await callback.message.edit_text(
        "🏆 <b>Leaderboard</b>\n\nFeature coming soon...",
        reply_markup=back_kb("menu")
    )
    await callback.answer()

@callback_router.callback_query(F.data == "menu_premium")
async def menu_premium_handler(callback: CallbackQuery) -> None:
    """जब यूज़र मेन्यू से 'Premium' चुनता है"""
    await callback.message.edit_text(
        "⭐ <b>Premium Subscription</b>\n\n"
        "Unlock all premium features:\n"
        "- Unlimited quizzes\n"
        "- Detailed analytics\n"
        "- Priority AI processing\n\n"
        "Contact admin for subscription.",
        reply_markup=back_kb("menu")
    )
    await callback.answer()

@callback_router.callback_query(F.data == "menu_help")
async def menu_help_handler(callback: CallbackQuery) -> None:
    """जब यूज़र मेन्यू से 'Help' चुनता है"""
    await callback.message.edit_text(
        "❓ <b>Help</b>\n\n"
        "Use /menu to see all features.\n"
        "Use /quiz for topic-wise quizzes.\n"
        "Use /dpp for Daily Practice Problems.\n"
        "Upload handwritten answers for AI evaluation.\n\n"
        "For any issues, contact @theteamvb.",
        reply_markup=back_kb("menu")
    )
    await callback.answer()

@callback_router.callback_query(F.data == "menu")
async def back_to_main_menu(callback: CallbackQuery) -> None:
    """किसी भी जगह से वापस मुख्य मेन्यू पर आने के लिए"""
    await callback.message.edit_text(
        "📋 <b>Main Menu</b>",
        reply_markup=main_menu_kb()
    )
    await callback.answer()
