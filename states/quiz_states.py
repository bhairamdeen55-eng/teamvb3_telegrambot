# states/quiz_states.py
from aiogram.fsm.state import StatesGroup, State

class QuizStates(StatesGroup):
    selecting_topic = State()
    starting_quiz = State()
    answering = State()
    reviewing_answer = State()
    completed = State()

class DPPStates(StatesGroup):
    selecting_topic = State()
    viewing_problem = State()
    viewing_solution = State()

class PhotoTestStates(StatesGroup):
    waiting_for_photo = State()
    processing = State()
    viewing_result = State()
