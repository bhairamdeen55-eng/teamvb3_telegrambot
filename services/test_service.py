# services/test_service.py
from typing import Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from db.crud import QuizCRUD, QuestionCRUD, AttemptCRUD, UserCRUD
from db.models import QuizAttempt, User, Test, UserTestAttempt
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


# ==================== DAILY TEST SCHEDULER HELPERS ====================

async def _get_daily_tests_for_user_session(session: AsyncSession, user_id: int, today: date):
    """Internal function to fetch or create daily 5 tests for a user."""
    # Check if user already has pending tests for today
    stmt = select(UserTestAttempt).where(
        UserTestAttempt.user_id == user_id,
        UserTestAttempt.date == today
    )
    result = await session.execute(stmt)
    attempts = result.scalars().all()
    
    if attempts:
        test_ids = [a.test_id for a in attempts if a.status == "pending"]
        if test_ids:
            stmt_tests = select(Test).where(Test.id.in_(test_ids))
            tests = (await session.execute(stmt_tests)).scalars().all()
            return tests
        else:
            return []   # All tests already done
    
    # No attempts for today → create 5 random tests
    stmt = select(Test).order_by(func.random()).limit(5)
    tests = (await session.execute(stmt)).scalars().all()
    if not tests:
        return []
    
    for test in tests:
        attempt = UserTestAttempt(
            user_id=user_id,
            test_id=test.id,
            date=today,
            status="pending"
        )
        session.add(attempt)
    await session.commit()
    return tests


async def get_daily_tests_for_user(user_id: int, session: Optional[AsyncSession] = None):
    """Fetch or create today's 5 tests for a specific user."""
    today = date.today()
    if session:
        return await _get_daily_tests_for_user_session(session, user_id, today)
    else:
        async with async_session_factory() as sess:
            return await _get_daily_tests_for_user_session(sess, user_id, today)


async def send_daily_tests(bot):
    """Send daily 5 tests to all active users (called by scheduler)."""
    async with async_session_factory() as session:
        users = await session.execute(select(User).where(User.is_active == True))
        user_list = users.scalars().all()
        logger.info(f"Sending daily tests to {len(user_list)} active users")
        
        for user in user_list:
            try:
                tests = await get_daily_tests_for_user(user.id, session)
                if tests:
                    from utils.keyboards import daily_tests_keyboard
                    await bot.send_message(
                        user.telegram_id,
                        "🌅 सुप्रभात! आज के आपके 5 टेस्ट तैयार हैं।",
                        reply_markup=daily_tests_keyboard(tests)
                    )
            except Exception as e:
                logger.error(f"Failed to send tests to {user.telegram_id}: {e}")
