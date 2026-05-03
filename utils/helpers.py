# utils/helpers.py
import re
import json
import hashlib
import base64
from datetime import datetime
from typing import Optional, Any, Union
from cryptography.fernet import Fernet
from config import settings
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from states.quiz_states import PhotoTestStates

# ─────────── पुराने helper ───────────
def sanitize_text(text: str) -> str:
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    return text.strip()

def truncate_text(text: str, max_length: int = 4096) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def parse_quiz_answer(text: str) -> Optional[str]:
    text = text.strip().upper()
    if text in ("A", "B", "C", "D"):
        return text
    match = re.match(r'^\s*(\d)\s*$', text)
    if match:
        idx = int(match.group(1)) - 1
        return chr(65 + idx) if 0 <= idx <= 3 else None
    match = re.match(r'^\s*OPTION\s*([A-D])\s*$', text, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return None

def encrypt_data(data: str) -> Optional[str]:
    if not settings.ENCRYPTION_KEY:
        return data
    try:
        key = settings.ENCRYPTION_KEY.encode() if len(settings.ENCRYPTION_KEY) == 44 else hashlib.sha256(settings.ENCRYPTION_KEY.encode()).digest()
        key = base64.urlsafe_b64encode(key) if len(key) != 32 else key
        if len(key) != 32:
            key = hashlib.sha256(key).digest()
        f = Fernet(base64.urlsafe_b64encode(key))
        return f.encrypt(data.encode()).decode()
    except Exception:
        return data

def decrypt_data(token: str) -> Optional[str]:
    if not settings.ENCRYPTION_KEY:
        return token
    try:
        key = settings.ENCRYPTION_KEY.encode() if len(settings.ENCRYPTION_KEY) == 44 else hashlib.sha256(settings.ENCRYPTION_KEY.encode()).digest()
        key = base64.urlsafe_b64encode(key) if len(key) != 32 else key
        if len(key) != 32:
            key = hashlib.sha256(key).digest()
        f = Fernet(base64.urlsafe_b64encode(key))
        return f.decrypt(token.encode()).decode()
    except Exception:
        return None

def format_time(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    if minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"

def calculate_percentage(correct: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((correct / total) * 100, 2)

def chunk_list(items: list, chunk_size: int = 10) -> list[list]:
    return [items[i:i+chunk_size] for i in range(0, len(items), chunk_size)]

# ─────────── नए helper (photo/pdf test के लिए) ───────────
def image_to_data_url(img_bytes: bytes, ext: str = "jpeg") -> str:
    b64 = base64.b64encode(img_bytes).decode("utf-8")
    return f"data:image/{ext};base64,{b64}"

def clean_json(text: str) -> str:
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    return text.strip()

def build_options_keyboard(current_q: dict):
    builder = InlineKeyboardBuilder()
    for i, opt in enumerate(current_q["options"]):
        label = f"{chr(65+i)}. {opt}"
        builder.button(text=label, callback_data=f"photo_answer:{i}")
    builder.button(text="⏹ End Test", callback_data="photo_end_test")
    builder.adjust(1)
    return builder.as_markup()

async def show_dashboard(message: Message, answers: list):
    total = len(answers)
    correct = sum(1 for a in answers if a["is_correct"])
    wrong = total - correct
    percentage = round((correct / total) * 100, 1) if total > 0 else 0
    text = (
        "📊 <b>Photo/PDF Test Dashboard</b>\n\n"
        f"✅ सही: {correct}\n"
        f"❌ गलत: {wrong}\n"
        f"📈 सटीकता: {percentage}%\n"
        f"📝 कुल प्रश्न: {total}\n\n"
        "<b>प्रत्येक प्रश्न का उत्तर:</b>\n"
    )
    for i, ans in enumerate(answers, 1):
        status = "✅" if ans["is_correct"] else "❌"
        selected_opt = ans["options"][ans["selected"]]
        correct_opt = ans["options"][ans["correct"]]
        text += (
            f"{status} Q{i}: {ans['question']}\n"
            f"   आपका: {selected_opt}\n"
            f"   सही: {correct_opt}\n"
            f"   व्याख्या: {ans['explanation']}\n\n"
        )
    await message.answer(text)

# ─────────── Shared Test Session Starter ───────────
async def start_shared_test_sessions(user_id: int, message: Message, state: FSMContext, questions: list):
    """किसी भी यूज़र के लिए शेयर्ड टेस्ट सेशन शुरू करें।"""
    await state.clear()
    await state.update_data(
        questions=questions,
        current_index=0,
        answers=[],
        total_questions=len(questions)
    )
    first_q = questions[0]
    await message.answer(
        f"📝 प्रश्न 1/{len(questions)}:\n\n{first_q['question']}",
        reply_markup=build_options_keyboard(first_q)
    )
    await state.set_state(PhotoTestStates.answering)
