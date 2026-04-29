# middlewares/throttling.py
import asyncio
import time
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from loguru import logger

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate: int = 3, burst: int = 5) -> None:
        self.rate = rate
        self.burst = burst
        self.user_timestamps: Dict[int, list[float]] = {}
        self.lock = asyncio.Lock()
        logger.info(f"Throttling initialized: rate={rate}/s, burst={burst}")

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None
        
        if user_id:
            async with self.lock:
                now = time.time()
                if user_id not in self.user_timestamps:
                    self.user_timestamps[user_id] = []
                
                timestamps = self.user_timestamps[user_id]
                timestamps = [t for t in timestamps if now - t < 1.0]
                self.user_timestamps[user_id] = timestamps
                
                if len(timestamps) >= self.burst:
                    logger.warning("Throttling user {} (burst limit)", user_id)
                    if isinstance(event, Message):
                        await event.answer("⚠️ Please slow down! You're sending too many requests.")
                    elif isinstance(event, CallbackQuery):
                        await event.answer("⚠️ Too fast! Please wait.", show_alert=True)
                    return
                
                timestamps.append(now)
                if len(timestamps) > self.rate:
                    sleep_time = 1.0 - (now - timestamps[-self.rate])
                    if sleep_time > 0:
                        await asyncio.sleep(sleep_time)
        
        return await handler(event, data)
