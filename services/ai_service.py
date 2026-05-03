# services/ai_service.py
import json
import base64
from typing import Optional, List
from openai import AsyncOpenAI
from loguru import logger
from config import settings

class AIService:
    def __init__(self):
        self.client = None
        if settings.OPENROUTER_API_KEY:
            self.client = AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=settings.openrouter_api_key_value,
            )
            logger.info("AI service initialized with provider: OpenRouter")
        else:
            logger.warning("No OpenRouter API key configured — AI features disabled")

    async def analyze_pdf(
        self,
        image_urls: List[str],
        prompt: str,
    ) -> Optional[str]:
        if not self.client:
            return None
        try:
            content = [{"type": "text", "text": prompt}]
            for url in image_urls:
                content.append({"type": "image_url", "image_url": {"url": url}})
            
            response = await self.client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=[{"role": "user", "content": content}],
                max_tokens=settings.AI_MAX_TOKENS,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"PDF analysis failed: {e}")
            return None

    async def analyze_image(
        self,
        image_url: str,
        prompt: str = "Analyze this image.",
    ) -> Optional[str]:
        if not self.client:
            return None
        try:
            response = await self.client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }],
                max_tokens=settings.AI_MAX_TOKENS,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return None

ai_service = AIService()
