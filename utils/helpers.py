# utils/helpers.py
import re
import json
import hashlib
from datetime import datetime
from typing import Optional, Any
from cryptography.fernet import Fernet
from config import settings

def sanitize_text(text: str) -> str:
    """Remove HTML/Telegram unsafe characters"""
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    return text.strip()

def truncate_text(text: str, max_length: int = 4096) -> str:
    """Truncate text to Telegram's message limit"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def parse_quiz_answer(text: str) -> Optional[str]:
    """Parse user's answer text to option letter (A/B/C/D)"""
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
    """Encrypt sensitive data if encryption key is set"""
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
    """Decrypt data if encryption key is set"""
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
    """Format seconds to readable time string"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    if minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"

def calculate_percentage(correct: int, total: int) -> float:
    """Calculate percentage score"""
    if total <= 0:
        return 0.0
    return round((correct / total) * 100, 2)

def chunk_list(items: list, chunk_size: int = 10) -> list[list]:
    """Split list into chunks"""
    return [items[i:i+chunk_size] for i in range(0, len(items), chunk_size)]

import base64
