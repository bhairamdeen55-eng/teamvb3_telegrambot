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
