# services/test_service.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from db.crud import QuizCRUD, QuestionCRUD, AttemptCRUD, UserCRUD
from db.database import async_session_factory
from services.ai_service import ai_service


class TestService:
    @staticmethod
    async def generate_ai_quiz(
        session: AsyncSession,
        topic: str,
        difficulty: str = "medium",
        count: int = 5,
        created_by: Optional[int] = None,
    ) -> Optional[int]:
        """Generate quiz using AI and save to database"""
        questions_data = await ai_service.generate_quiz(topic, difficulty, count)
        if not questions_data:
            logger.warning("AI quiz generation returned no data for topic: {}", topic)
            return None

        quiz = await QuizCRUD.create(
            session,
            title=f"AI Quiz: {topic.title()}",
            description=f"AI-generated {difficulty} quiz on {topic}",
            topic=topic,
            difficulty=difficulty,
            question_count=len(questions_data),
            created_by=created_by,
            metadata_json={"source": "ai", "model": ai_service.client.model if ai_service.client else "unknown"},
        )

        await QuestionCRUD.bulk_create(session, quiz.id, questions_data)
        logger.info("AI quiz created: ID={} Topic={} Questions={}", quiz.id, topic, len(questions_data))

        return quiz.id

    @staticmethod
    async def evaluate_photo_test(
        session: AsyncSession,
        user_id: int,
        image_url: str,
        subject: Optional[str] = None,
    ) -> Optional[dict]:
        """Evaluate a photo/submission using AI vision"""
        prompt = (
            f"Analyze this student's {subject or 'test'} submission photo. "
            "Evaluate: 1) Content accuracy 2) Presentation 3) Completeness. "
            "Provide scores out of 10 for each category and overall feedback."
        )

        result = await ai_service.analyze_image(image_url, prompt)
        if not result:
            return None

        return {
            "user_id": user_id,
            "result": result,
            "subject": subject,
        }

    @staticmethod
    async def get_user_performance_summary(session: AsyncSession, user_id: int) -> dict:
        """Get comprehensive user performance summary"""
        stats = await AttemptCRUD.get_user_stats(session, user_id)
        user = await UserCRUD.get(session, user_id)

        summary = {
            "total_attempts": stats["total_attempts"],
            "avg_percentage": stats["avg_percentage"],
            "total_correct": stats["total_correct"],
            "total_wrong": stats["total_wrong"],
            "accuracy": 0.0,
            "subscription_tier": user.subscription_tier.value if user else "free",
        }

        total_answered = stats["total_correct"] + stats["total_wrong"]
        if total_answered > 0:
            summary["accuracy"] = round((stats["total_correct"] / total_answered) * 100, 2)

        return summary


# ==================== DAILY TEST SCHEDULER ====================

async def send_daily_tests(bot):
    """
    फ़िलहाल डेली टेस्ट भेजने का लॉजिक पूरी तरह से सेफ़ है।
    जब तक ज़रूरी मॉडल (Test, UserTestAttempt) नहीं बन जाते, यह सिर्फ़ लॉग करेगा।
    """
    logger.info("Daily test job triggered — but no Test/UserTestAttempt model yet. Skipping.")
    # TODO: जब db.models में Test और UserTestAttempt जुड़ जाएँ, तब नीचे का कोड अनकमेंट करें
    # from db.models import Quiz, QuizAttempt
    # ... असली लॉजिक यहाँ
