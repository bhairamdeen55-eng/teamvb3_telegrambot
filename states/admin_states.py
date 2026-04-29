# states/admin_states.py
from aiogram.fsm.state import StatesGroup, State

class AdminStates(StatesGroup):
    main_menu = State()
    broadcasting = State()
    managing_users = State()
    managing_quizzes = State()
    creating_quiz = State()
    adding_questions = State()
    managing_dpps = State()
    managing_subscriptions = State()
    viewing_stats = State()
    broadcast_text = State()
    broadcast_confirm = State()
