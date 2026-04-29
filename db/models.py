# db/models.py
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, Float, Text, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from db.database import Base
import enum

class UserRole(str, enum.Enum):
    USER = "user"
    PREMIUM = "premium"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"

class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class User(Base):
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True, autoincrement=False)
    username = Column(String(255), nullable=True, index=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE, nullable=False)
    subscription_expiry = Column(DateTime, nullable=True)
    daily_quiz_count = Column(Integer, default=0)
    last_quiz_date = Column(DateTime, nullable=True)
    total_quizzes = Column(Integer, default=0)
    total_score = Column(Float, default=0.0)
    is_blocked = Column(Boolean, default=False)
    language = Column(String(10), default="en")
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    subscriptions = relationship("Subscription", back_populates="user", lazy="selectin")
    quiz_attempts = relationship("QuizAttempt", back_populates="user", lazy="selectin")
    
    @property
    def is_premium(self) -> bool:
        return self.subscription_tier != SubscriptionTier.FREE and self.subscription_expiry and self.subscription_expiry > datetime.utcnow()
    
    @property
    def is_admin(self) -> bool:
        return self.role in (UserRole.ADMIN, UserRole.SUPERADMIN)

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    tier = Column(Enum(SubscriptionTier), nullable=False)
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=False)
    payment_id = Column(String(255), nullable=True)
    amount = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="subscriptions")

class Quiz(Base):
    __tablename__ = "quizzes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    topic = Column(String(255), nullable=True, index=True)
    difficulty = Column(String(50), default="medium")
    question_count = Column(Integer, default=0)
    time_limit = Column(Integer, nullable=True)
    created_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    questions = relationship("Question", back_populates="quiz", lazy="selectin", cascade="all, delete-orphan")
    attempts = relationship("QuizAttempt", back_populates="quiz", lazy="selectin")

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)
    correct_answer = Column(String(10), nullable=False)
    explanation = Column(Text, nullable=True)
    marks = Column(Float, default=1.0)
    question_type = Column(String(50), default="mcq")
    order = Column(Integer, default=0)
    
    quiz = relationship("Quiz", back_populates="questions")

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    score = Column(Float, default=0.0)
    total_marks = Column(Float, default=0.0)
    percentage = Column(Float, default=0.0)
    correct_count = Column(Integer, default=0)
    wrong_count = Column(Integer, default=0)
    unanswered = Column(Integer, default=0)
    time_taken = Column(Integer, nullable=True)
    answers = Column(JSON, nullable=True)
    completed = Column(Boolean, default=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="quiz_attempts")
    quiz = relationship("Quiz", back_populates="attempts")

class DPP(Base):
    __tablename__ = "dpps"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    topic = Column(String(255), nullable=True, index=True)
    difficulty = Column(String(50), default="medium")
    problem_count = Column(Integer, default=0)
    content = Column(JSON, nullable=True)
    pdf_url = Column(String(500), nullable=True)
    solution_url = Column(String(500), nullable=True)
    created_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class PhotoTest(Base):
    __tablename__ = "photo_tests"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    photo_url = Column(String(500), nullable=False)
    result = Column(JSON, nullable=True)
    score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
