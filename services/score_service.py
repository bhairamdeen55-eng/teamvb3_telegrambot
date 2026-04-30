# services/score_service.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from loguru import logger
from db.models import User, QuizAttempt
from db.crud import AttemptCRUD

class ScoreService:
    @staticmethod
    async def get_user_rank(session: AsyncSession, user_id: int) -> Optional[int]:
        """Get user's rank based on average percentage"""
        result = await session.execute(
            select(
                User.id,
                func.avg(QuizAttempt.percentage).label("avg_score")
            )
            .join(QuizAttempt, QuizAttempt.user_id == User.id)
            .where(QuizAttempt.completed == True)
            .group_by(User.id)
            .order_by(desc("avg_score"))
        )
        rankings = list(result.all())
        for i, row in enumerate(rankings, 1):
            if row[0] == user_id:
                return i
        return None

    @staticmethod
    async def get_leaderboard(
        session: AsyncSession,
        limit: int = 10,
    ) -> list[dict]:
        """Get top users by average score"""
        result = await session.execute(
            select(
                User.id,
                User.username,
                User.first_name,
                func.avg(QuizAttempt.percentage).label("avg_score"),
                func.count(QuizAttempt.id).label("total_attempts"),
            )
            .join(QuizAttempt, QuizAttempt.user_id == User.id)
            .where(QuizAttempt.completed == True)
            .group_by(User.id)
            .order_by(desc("avg_score"))
            .limit(limit)
        )
        return [
            {
                "rank": i + 1,
                "user_id": row[0],
                "username": row[1],
                "name": row[2],
                "avg_score": round(row[3] or 0, 2),
                "attempts": row[4] or 0,
            }
            for i, row in enumerate(result.all())
        ]

    @staticmethod
    async def check_and_update_achievements(session: AsyncSession, user_id: int) -> list[str]:
        """Check for new achievements"""
        stats = await AttemptCRUD.get_user_stats(session, user_id)
        new_achievements = []
        
        if stats["total_attempts"] == 1:
            new_achievements.append("🎯 First Quiz Complete!")
        if stats["total_attempts"] >= 10:
            new_achievements.append("🔥 10 Quizzes Done!")
        if stats["avg_percentage"] >= 90:
            new_achievements.append("🏆 Top Scorer!")
        if stats["total_attempts"] >= 50:
            new_achievements.append("💪 50 Quizzes — Dedicated Learner!")
        if stats["total_correct"] >= 100:
            new_achievements.append("🎯 100 Correct Answers!")
        
        return new_achievements
