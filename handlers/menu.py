# handlers/menu.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from loguru import logger
from utils.texts import MENU_TEXT, QUIZ_INTRO, DPP_INTRO, PHOTO_TEST_INTRO, HELP_TEXT
from utils.keyboards import main_menu_kb, topic_kb, back_kb, admin_menu_kb
from db.crud import AttemptCRUD

menu_router = Router()

@menu_router.callback_query(F.data == "menu")
async def main_menu_callback(callback: CallbackQuery) -> None:
    await callback.message.edit_text(MENU_TEXT, reply_markup=main_menu_kb())
    await callback.answer()

@menu_router.callback_query(F.data == "menu_quiz")
async def quiz_menu_callback(callback: CallbackQuery) -> None:
    topics = ["Mathematics", "Physics", "Chemistry", "Biology", "Computer Science", "English", "GK"]
    await callback.message.edit_text(QUIZ_INTRO, reply_markup=topic_kb(topics, "quiz_topic"))
    await callback.answer()

@menu_router.callback_query(F.data == "menu_dpp")
async def dpp_menu_callback(callback: CallbackQuery) -> None:
    topics = ["Mathematics", "Physics", "Chemistry", "Biology", "Computer Science"]
    await callback.message.edit_text(DPP_INTRO, reply_markup=topic_kb(topics, "dpp_topic"))
    await callback.answer()

@menu_router.callback_query(F.data == "menu_photo")
async def photo_menu_callback(callback: CallbackQuery) -> None:
    await callback.message.edit_text(PHOTO_TEST_INTRO, reply_markup=back_kb("menu"))
    await callback.answer()

@menu_router.callback_query(F.data == "menu_scores")
async def scores_callback(callback: CallbackQuery, user=None, session=None) -> None:
    if not user or not session:
        await callback.answer("⚠️ Session error", show_alert=True)
        return
    stats = await AttemptCRUD.get_user_stats(session, user.id)
    text = (
        "📊 <b>Your Performance</b>\n\n"
        f"Total Quizzes: {stats['total_attempts']}\n"
        f"Average Score: {stats['avg_percentage']}%\n"
        f"Correct Answers: {stats['total_correct']}\n"
        f"Wrong Answers: {stats['total_wrong']}\n\n"
        "Keep practicing to improve!"
    )
    await callback.message.edit_text(text, reply_markup=back_kb("menu"))
    await callback.answer()

@menu_router.callback_query(F.data == "menu_leaderboard")
async def leaderboard_callback(callback: CallbackQuery, session=None) -> None:
    text = "🏆 <b>Leaderboard</b>\n\nComing soon..."
    await callback.message.edit_text(text, reply_markup=back_kb("menu"))
    await callback.answer()

@menu_router.callback_query(F.data == "menu_premium")
async def premium_callback(callback: CallbackQuery) -> None:
    text = (
        "⭐ <b>Premium Subscription</b>\n\n"
        "🔹 Unlimited quizzes\n"
        "🔹 Advanced analytics\n"
        "🔹 Priority support\n"
        "🔹 Ad-free experience\n\n"
        "Contact @admin to upgrade!"
    )
    await callback.message.edit_text(text, reply_markup=back_kb("menu"))
    await callback.answer()

@menu_router.callback_query(F.data == "menu_help")
async def help_callback(callback: CallbackQuery) -> None:
    await callback.message.edit_text(HELP_TEXT, reply_markup=back_kb("menu"))
    await callback.answer()
