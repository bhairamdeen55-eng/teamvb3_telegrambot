import io
import json
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from loguru import logger
from services.ai_service import ai_service
from states.quiz_states import PhotoTestStates
from utils.helpers import image_to_data_url, clean_json, build_options_keyboard, show_dashboard

photo_test_router = Router()

@photo_test_router.message(F.photo)
async def handle_photo(message: Message, state: FSMContext) -> None:
    await state.set_state(PhotoTestStates.processing)
    status_msg = await message.answer("📸 AI आपकी फोटो पढ़ रहा है... कृपया प्रतीक्षा करें।")

    try:
        photo = message.photo[-1]
        file = await message.bot.get_file(photo.file_id)
        file_bytes = io.BytesIO()
        await message.bot.download_file(file.file_path, destination=file_bytes)
        file_bytes.seek(0)
        data_url = image_to_data_url(file_bytes.read())

        prompt = (
            "यह एक शैक्षणिक फोटो है। कृपया इस फोटो में दिख रहे सभी प्रश्नों, उनके विकल्पों और सही उत्तरों को पहचानें।\n"
            "अगर किसी प्रश्न के विकल्प नहीं दिए गए हैं, तो खुद 4 उचित विकल्प (A, B, C, D) बनाएं और सही उत्तर चिह्नित करें।\n"
            "अपना जवाब **केवल JSON** फ़ॉर्मेट में दें, बिना किसी अन्य टेक्स्ट के:\n"
            '[\n  {\n    "question": "प्रश्न का टेक्स्ट",\n    "options": ["विकल्प A", "विकल्प B", "विकल्प C", "विकल्प D"],\n    "correct_answer": 0 (सही विकल्प का index, 0 से 3),\n    "explanation": "उत्तर की व्याख्या (वैकल्पिक)"\n  }\n]'
        )

        ai_response = await ai_service.analyze_image(data_url, prompt)
        if not ai_response:
            raise ValueError("AI ने कोई जवाब नहीं दिया")

        questions = json.loads(clean_json(ai_response))
        if not isinstance(questions, list) or len(questions) == 0:
            raise ValueError("AI ने मान्य प्रश्न नहीं लौटाए")

        await state.update_data(
            questions=questions,
            current_index=0,
            answers=[],
            total_questions=len(questions)
        )
        first_q = questions[0]
        await status_msg.edit_text(
            f"📝 प्रश्न 1/{len(questions)}:\n\n{first_q['question']}",
            reply_markup=build_options_keyboard(first_q)
        )
        await state.set_state(PhotoTestStates.answering)

    except Exception as e:
        logger.error(f"Photo test error: {e}")
        await status_msg.edit_text("❌ फोटो को प्रोसेस करने में त्रुटि। कृपया स्पष्ट फोटो भेजें या बाद में प्रयास करें।")
        await state.clear()

@photo_test_router.callback_query(F.data.startswith("photo_answer:"), PhotoTestStates.answering)
async def process_answer(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    questions = data["questions"]
    current_idx = data["current_index"]
    answers = data.get("answers", [])

    selected_idx = int(callback.data.split(":")[1])
    correct_idx = questions[current_idx]["correct_answer"]
    is_correct = (selected_idx == correct_idx)

    answers.append({
        "question": questions[current_idx]["question"],
        "selected": selected_idx,
        "correct": correct_idx,
        "is_correct": is_correct,
        "options": questions[current_idx]["options"],
        "explanation": questions[current_idx].get("explanation", "")
    })

    current_idx += 1
    await state.update_data(current_index=current_idx, answers=answers)

    if current_idx >= len(questions):
        await show_dashboard(callback.message, answers)
        await state.clear()
    else:
        next_q = questions[current_idx]
        await callback.message.edit_text(
            f"📝 प्रश्न {current_idx+1}/{len(questions)}:\n\n{next_q['question']}",
            reply_markup=build_options_keyboard(next_q)
        )

@photo_test_router.callback_query(F.data == "photo_end_test", PhotoTestStates.answering)
async def end_test(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    answers = data.get("answers", [])
    await show_dashboard(callback.message, answers)
    await state.clear()
