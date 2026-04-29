# handlers/photo_test.py
import os
import aiofiles
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from loguru import logger
from states.quiz_states import PhotoTestStates
from utils.keyboards import back_kb
from config import settings

photo_test_router = Router()

@photo_test_router.message(F.photo)
async def handle_photo(message: Message, state: FSMContext, session=None, user=None) -> None:
    await state.set_state(PhotoTestStates.processing)
    
    processing_msg = await message.answer("📸 Processing your image... Please wait.")
    
    try:
        photo = message.photo[-1]
        file = await message.bot.get_file(photo.file_id)
        
        # Save photo
        photo_dir = settings.DATA_DIR / "photos"
        photo_dir.mkdir(parents=True, exist_ok=True)
        file_path = photo_dir / f"{user.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jpg"
        
        await message.bot.download_file(file.file_path, destination=str(file_path))
        
        # Placeholder for AI processing
        result_text = (
            "📸 <b>Photo Analysis Result</b>\n\n"
            f"✅ Image received and saved\n"
            f"📏 Size: {photo.width}x{photo.height}\n"
            f"📂 File: {file_path.name}\n\n"
            "🔄 AI analysis will be integrated here."
        )
        
        await processing_msg.edit_text(result_text, reply_markup=back_kb("menu"))
        
    except Exception as e:
        logger.error("Photo processing failed: {}", e)
        await processing_msg.edit_text(
            "❌ Failed to process image. Please try again.",
            reply_markup=back_kb("menu"),
        )
    
    await state.clear()

@photo_test_router.message(F.document)
async def handle_document(message: Message, state: FSMContext) -> None:
    if message.document and message.document.mime_type and "image" in message.document.mime_type:
        await handle_photo(message, state)
    else:
        await message.answer(
            "⚠️ Please send an image file (JPG/PNG).",
            reply_markup=back_kb("menu"),
        )
