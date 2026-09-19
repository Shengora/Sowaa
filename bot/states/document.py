from aiogram.fsm.state import State, StatesGroup

class DocumentFillingState(StatesGroup):
    picking_template = State()
    answering_questions = State()
