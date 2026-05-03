# services/ai_service.py
import json
from typing import Optional, List
from openai import AsyncOpenAI
from loguru import logger
from config import settings

class AIService:
    def __init__(self):
        self.client = None
        if settings.AI_API_KEY:
            api_key = settings.AI_API_KEY.get_secret_value()
            self.client = AsyncOpenAI(api_key=api_key)
            logger.info("AI service initialized with provider: {}", settings.AI_PROVIDER)
        else:
            logger.warning("No AI API key configured — AI features disabled")

    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Optional[str]:
        if not self.client:
            return None
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = await self.client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=messages,
                max_tokens=max_tokens or settings.AI_MAX_TOKENS,
                temperature=temperature or settings.AI_TEMPERATURE,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("AI generation failed: {}", e)
            return None

    async def analyze_image(
        self,
        image_url: str,
        prompt: str = "Analyze this image and provide detailed feedback.",
    ) -> Optional[str]:
        """एक ही इमेज को analyze करने के लिए।"""
        if not self.client:
            return None
        try:
            response = await self.client.chat.completions.create(
                model=settings.VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": image_url}},
                        ],
                    }
                ],
                max_tokens=settings.AI_MAX_TOKENS,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("Image analysis failed: {}", e)
            return None

    async def analyze_pdf(
        self,
        image_urls: List[str],   # base64 data URLs की list
        prompt: str,
        max_tokens: Optional[int] = None,
    ) -> Optional[str]:
        """एक साथ कई इमेज (PDF pages) भेजने के लिए।"""
        if not self.client:
            return None
        try:
            content = [{"type": "text", "text": prompt}]
            for url in image_urls:
                content.append({"type": "image_url", "image_url": {"url": url}})
            response = await self.client.chat.completions.create(
                model=settings.VISION_MODEL,
                messages=[{"role": "user", "content": content}],
                max_tokens=max_tokens or settings.AI_MAX_TOKENS,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("PDF analysis failed: {}", e)
            return None

    async def generate_quiz(
        self,
        topic: str,
        difficulty: str = "medium",
        count: int = 5,
    ) -> Optional[list[dict]]:
        prompt = (
            f"Generate {count} {difficulty}-difficulty multiple choice questions about {topic}. "
            "Return ONLY valid JSON array with objects containing: "
            "question_text, options (array of 4 strings), correct_answer (A/B/C/D), explanation, marks (float)."
        )
        response = await self.generate_response(prompt, system_prompt="You are a quiz generator. Return only valid JSON.")
        if response:
            try:
                json_str = response.strip()
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error("Failed to parse quiz JSON: {}", e)
                return None
        return None

ai_service = AIService()
