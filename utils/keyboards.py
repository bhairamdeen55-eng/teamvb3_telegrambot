# utils/keyboards.py
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Optional

def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🧠 Quiz", callback_data="menu_quiz")
    builder.button(text="📚 DPP", callback_data="menu_dpp")
    builder.button(text="📸 Photo Test", callback_data="menu_photo")
    builder.button(text="📊 My Scores", callback_data="menu_scores")
    builder.button(text="🏆 Leaderboard", callback_data="menu_leaderboard")
    builder.button(text="⭐ Premium", callback_data="menu_premium")
    builder.button(text="❓ Help", callback_data="menu_help")
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()

def back_kb(callback_prefix: str = "menu") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Back", callback_data=callback_prefix)
    return builder.as_markup()

def yes_no_kb(callback_yes: str, callback_no: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Yes", callback_data=callback_yes)
    builder.button(text="❌ No", callback_data=callback_no)
    builder.adjust(2)
    return builder.as_markup()

def confirmation_kb(confirm_callback: str, cancel_callback: str = "menu") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Confirm", callback_data=confirm_callback)
    builder.button(text="❌ Cancel", callback_data=cancel_callback)
    builder.adjust(2)
    return builder.as_markup()

def topic_kb(topics: list[str], callback_prefix: str = "topic") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for topic in topics:
        builder.button(text=topic, callback_data=f"{callback_prefix}_{topic}")
    builder.button(text="🎲 Random", callback_data=f"{callback_prefix}_random")
    builder.button(text="🔙 Back", callback_data="menu")
    builder.adjust(2, 2, 1)
    return builder.as_markup()

def pagination_kb(current: int, total: int, prefix: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if current > 0:
        builder.button(text="⬅️", callback_data=f"{prefix}_prev_{current}")
    builder.button(text=f"{current+1}/{total}", callback_data="noop")
    if current < total - 1:
        builder.button(text="➡️", callback_data=f"{prefix}_next_{current}")
    builder.button(text="🔙 Back", callback_data="menu")
    builder.adjust(3, 1)
    return builder.as_markup()

def admin_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Statistics", callback_data="admin_stats")
    builder.button(text="📢 Broadcast", callback_data="admin_broadcast")
    builder.button(text="👥 Manage Users", callback_data="admin_users")
    builder.button(text="📝 Manage Quizzes", callback_data="admin_quizzes")
    builder.button(text="📚 Manage DPPs", callback_data="admin_dpps")
    builder.button(text="⭐ Manage Subs", callback_data="admin_subs")
    builder.button(text="🔙 Back", callback_data="menu")
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()

def remove_kb() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
