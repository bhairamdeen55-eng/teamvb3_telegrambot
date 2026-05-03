# handlers/pdf_test.py
import io
import json
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from loguru import logger
import fitz
from services.ai_service import ai_service
from states.quiz_states import PhotoTestStates
from utils.helpers import image_to_data_url, clean_json, build_options_keyboard, show_dashboard, start_shared_test_sessions
from db.database import async_session_factory
from db.models import SharedTest
from sqlalchemy import select
from config import settings

pdf_test_router = Router()

@pdf_test_router.message(F.document)
async def handle_pdf(message: Message, state: FSMContext) -> None:
    if not message.document.mime_type or "pdf" not in message.document.mime_type:
        await message.answer("⚠️ कृपया केवल PDF फाइल भेजें।")
        return

    await state.set_state(PhotoTestStates.processing)
    status_msg = await message.answer("📄 AI आपकी PDF पढ़ रहा है... कृपया प्रतीक्षा करें।")

    try:
        file = await message.bot.get_file(message.document.file_id)
        file_bytes = io.BytesIO()
        await message.bot.download_file(file.file_path, destination=file_bytes)
        file_bytes.seek(0)

        doc = fitz.open(stream=file_bytes.read(), filetype="pdf")
        image_urls = []
        max_pages = min(len(doc), 10)
        for page_num in range(max_pages):
            page = doc[page_num]
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("jpeg")
            data_url = image_to_data_url(img_bytes, ext="jpeg")
            image_urls.append(data_url)
        doc.close()

        if not image_urls:
            raise ValueError("PDF में कोई पेज नहीं मिला")

        prompt = (
            "यह एक शैक्षणिक PDF है। कृपया इस PDF के **सभी** प्रश्नों, उनके विकल्पों और सही उत्तरों को पहचानें।\n"
            "अगर किसी प्रश्न के विकल्प नहीं दिए गए हैं, तो खुद 4 उचित विकल्प (A, B, C, D) बनाएं और सही उत्तर चिह्नित करें।\n"
            "अपना जवाब **केवल JSON** फ़ॉर्मेट में दें, बिना किसी अन्य टेक्स्ट के:\n"
            '[\n  {\n    "question": "प्रश्न का टेक्स्ट",\n    "options": ["विकल्प A", "विकल्प B", "विकल्प C", "विकल्प D"],\n    "correct_answer": 0 (सही विकल्प का index, 0 से 3),\n    "explanation": "उत्तर की व्याख्या (वैकल्पिक)"\n  }\n]'
        )

        ai_response = await ai_service.analyze_pdf(image_urls, prompt)
        if not ai_response:
            raise ValueError("AI ने कोई जवाब नहीं दिया")

        questions = json.loads(clean_json(ai_response))
        if not isinstance(questions, list) or len(questions) == 0:
            raise ValueError("AI ने मान्य प्रश्न नहीं लौटाए")

        code = SharedTest.generate_code()
        expires = datetime.utcnow() + timedelta(hours=48)

        async with async_session_factory() as session:
            shared = SharedTest(
                code=code,
                questions=questions,
                created_by=message.from_user.id,
                expires_at=expires
            )
            session.add(shared)
            await session.commit()

        bot_username = (await message.bot.me()).username
        deep_link = f"https://t.me/{bot_username}?start=test_{code}"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚀 इस टेस्ट को खुद खेलें", callback_data=f"start_shared_test:{code}")],
            [InlineKeyboardButton(text="📋 लिंक कॉपी करें (टैप करें)", url=deep_link)]
        ])

        await status_msg.edit_text(
            f"✅ <b>लाइव टेस्ट तैयार!</b>\n\n"
            f"⏰ यह लिंक 48 घंटे तक valid रहेगा।\n"
            f"🔗 नीचे बटन से आप खुद भी टेस्ट दे सकते हैं।",
            reply_markup=keyboard
        )
        await state.clear()

    except Exception as e:
        logger.error(f"PDF test error: {e}")
        await status_msg.edit_text("❌ PDF को प्रोसेस करने में त्रुटि। कृपया स्पष्ट PDF भेजें या बाद में प्रयास करें।")
        await state.clear()

@pdf_test_router.callback_query(F.data.startswith("start_shared_test:"))
async def start_shared_test_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    code = callback.data.split(":", 1)[1]

    async with async_session_factory() as session:
        result = await session.execute(select(SharedTest).where(SharedTest.code == code))
        shared_test = result.scalar_one_or_none()

        if not shared_test:
            await callback.message.answer("❌ टेस्ट नहीं मिला।")
            return

        if shared_test.expires_at < datetime.utcnow():
            await callback.message.answer("⏰ यह टेस्ट expired हो गया है।")
            return

        await start_shared_test_sessions(
            user_id=callback.from_user.id,
            message=callback.message,
            state=state,
            questions=shared_test.questions
        )
