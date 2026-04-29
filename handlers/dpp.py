# handlers/dpp.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from loguru import logger
from states.quiz_states import DPPStates
from utils.keyboards import back_kb, topic_kb
from db.crud import DPPCRUD

dpp_router = Router()

@dpp_router.callback_query(F.data.startswith("dpp_topic_"))
async def dpp_topic_selected(callback: CallbackQuery, state: FSMContext, session=None) -> None:
    topic = callback.data.replace("dpp_topic_", "")
    await state.update_data(topic=topic)
    
    dpps = await DPPCRUD.get_by_topic(session, topic) if topic != "random" else []
    
    if not dpps:
        await callback.message.edit_text(
            "❌ No problems available for this topic yet.",
            reply_markup=back_kb("menu_dpp"),
        )
        await callback.answer()
        return
    
    dpp = dpps[0]
    text = (
        f"📚 <b>{dpp.title}</b>\n\n"
        f"Topic: {dpp.topic}\n"
        f"Difficulty: {dpp.difficulty}\n"
        f"Problems: {dpp.problem_count}\n\n"
        f"{dpp.content.get('description', '') if dpp.content else ''}"
    )
    
    await callback.message.edit_text(text, reply_markup=back_kb("menu_dpp"))
    await callback.answer()
