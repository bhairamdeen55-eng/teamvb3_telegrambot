# handlers/quiz.py
import random
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func
from loguru import logger
from states.quiz_states import QuizStates
from utils.keyboards import back_kb, topic_kb, pagination_kb
from utils.helpers import parse_quiz_answer, calculate_percentage
from db.models import Quiz, Question, QuizAttempt
from db.crud import QuizCRUD, QuestionCRUD, AttemptCRUD, UserCRUD

quiz_router = Router()

@quiz_router.callback_query(F.data.startswith("quiz_topic_"))
async def topic_selected(callback: CallbackQuery, state: FSMContext, session=None) -> None:
    topic = callback.data.replace("quiz_topic_", "")
    await state.update_data(topic=topic)
    
    if topic == "random":
        quizzes = await QuizCRUD.get_random(session, limit=1)
    else:
        quizzes = await QuizCRUD.get_by_topic(session, topic)
    
    if not quizzes:
        await callback.message.edit_text(
            "❌ No quizzes available for this topic.",
            reply_markup=back_kb("menu_quiz"),
        )
        await callback.answer()
        return
    
    quiz = random.choice(quizzes)
    questions = await QuestionCRUD.get_by_quiz(session, quiz.id)
    
    if not questions:
        await callback.message.edit_text(
            "❌ This quiz has no questions.",
            reply_markup=back_kb("menu_quiz"),
        )
        await callback.answer()
        return
    
    random.shuffle(questions)
    await state.update_data(
        quiz_id=quiz.id,
        questions=[{"id": q.id, "correct": q.correct_answer, "marks": q.marks} for q in questions],
        current_q=0,
        answers={},
        score=0.0,
        total_marks=sum(q.marks for q in questions),
        start_time=datetime.utcnow().isoformat(),
    )
    
    await state.set_state(QuizStates.answering)
    await show_question(callback.message, state, session, 0)
    await callback.answer()

async def show_question(message: Message, state: FSMContext, session, idx: int) -> None:
    data = await state.get_data()
    questions_data = data.get("questions", [])
    
    if idx >= len(questions_data):
        await finish_quiz(message, state, session)
        return
    
    q_data = questions_data[idx]
    question = await session.get(Question, q_data["id"])
    if not question:
        await message.answer("❌ Question not found.", reply_markup=back_kb("menu"))
        return
    
    options_text = ""
    for i, opt in enumerate(question.options):
        letter = chr(65 + i)
        selected = "✅ " if q_data["id"] in data.get("answers", {}) and data["answers"][q_data["id"]] == letter else ""
        options_text += f"{selected}<b>{letter}.</b> {opt}\n"
    
    text = (
        f"<b>Question {idx + 1}/{len(questions_data)}</b>\n\n"
        f"{question.question_text}\n\n"
        f"{options_text}\n"
        f"📝 Reply with A, B, C, or D"
    )
    
    # Pagination keyboard
    builder_kb = pagination_kb(idx, len(questions_data), "q")
    await message.edit_text(text, reply_markup=builder_kb)

@quiz_router.message(QuizStates.answering)
async def handle_answer(message: Message, state: FSMContext, session=None) -> None:
    answer = parse_quiz_answer(message.text)
    if not answer:
        await message.answer("⚠️ Please reply with A, B, C, or D")
        return
    
    data = await state.get_data()
    questions = data.get("questions", [])
    current = data.get("current_q", 0)
    answers = data.get("answers", {})
    score = data.get("score", 0.0)
    
    q_data = questions[current]
    answers[q_data["id"]] = answer
    
    if answer == q_data["correct"]:
        score += q_data["marks"]
    
    await state.update_data(answers=answers, score=score, current_q=current + 1)
    
    if current + 1 >= len(questions):
        await finish_quiz(message, state, session)
    else:
        await show_question(message, state, session, current + 1)

@quiz_router.callback_query(F.data.startswith("q_"), QuizStates.answering)
async def quiz_pagination(callback: CallbackQuery, state: FSMContext, session=None) -> None:
    parts = callback.data.split("_")
    action = parts[1]
    current = int(parts[2]) if len(parts) > 2 else 0
    
    data = await state.get_data()
    questions = data.get("questions", [])
    
    if action == "next":
        new_idx = current + 1
    elif action == "prev":
        new_idx = current - 1
    else:
        new_idx = current
    
    if 0 <= new_idx < len(questions):
        await state.update_data(current_q=new_idx)
        await show_question(callback.message, state, session, new_idx)
    
    await callback.answer()

async def finish_quiz(message: Message, state: FSMContext, session=None) -> None:
    data = await state.get_data()
    score = data.get("score", 0.0)
    total_marks = data.get("total_marks", 1.0)
    quiz_id = data.get("quiz_id")
    user = data.get("user")
    answers = data.get("answers", {})
    
    percentage = calculate_percentage(score, total_marks) if total_marks > 0 else 0
    questions_data = data.get("questions", [])
    correct = sum(1 for q in questions_data if answers.get(q["id"]) == q["correct"])
    wrong = sum(1 for q in questions_data if answers.get(q["id"]) and answers[q["id"]] != q["correct"])
    unanswered = len(questions_data) - len(answers)
    
    # Save attempt
    if session and user:
        try:
            await AttemptCRUD.create(
                session,
                user_id=user.id,
                quiz_id=quiz_id,
                score=score,
                total_marks=total_marks,
                percentage=percentage,
                correct_count=correct,
                wrong_count=wrong,
                unanswered=unanswered,
                answers=answers,
                completed=True,
                completed_at=datetime.utcnow(),
            )
            await UserCRUD.increment_daily_quiz(session, user.id)
        except Exception as e:
            logger.error("Failed to save attempt: {}", e)
    
    text = (
        "🎯 <b>Quiz Complete!</b>\n\n"
        f"✅ Correct: {correct}\n"
        f"❌ Wrong: {wrong}\n"
        f"⬜ Unanswered: {unanswered}\n"
        f"📊 Score: {score}/{total_marks} ({percentage}%)\n\n"
        "Keep practicing!"
    )
    
    await message.answer(text, reply_markup=back_kb("menu"))
    await state.clear()
