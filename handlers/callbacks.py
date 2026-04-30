# handlers/callbacks.py
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
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
