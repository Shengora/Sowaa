import pytest
import pytest_asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from aiogram.types import Message, CallbackQuery, User as AiogramUser
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from bot.database.core import Base
from bot.database.models import User, Lawyer, Client, Role, DocumentTemplate
from bot.handlers.client.document import answer_question, pick_template
from bot.seed_template import create_example_docx

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session

@pytest_asyncio.fixture
async def setup_data(db_session):
    user_lawyer = User(telegram_id=111, role=Role.lawyer)
    db_session.add(user_lawyer)
    await db_session.flush()

    lawyer = Lawyer(user_id=user_lawyer.id, invite_token="test_lawyer")
    db_session.add(lawyer)
    await db_session.flush()

    user_client = User(telegram_id=222, role=Role.client)
    db_session.add(user_client)
    await db_session.flush()

    client = Client(user_id=user_client.id, lawyer_id=lawyer.id)
    db_session.add(client)
    await db_session.flush()

    create_example_docx("test_template.docx")

    questions = [
        {"key": "passport_number", "question": "Passport?", "type": "text", "validation": "^[A-Za-z]{2}\\d{7}$"},
        {"key": "date", "question": "Date?", "type": "text", "validation": "^\\d{2}\\.\\d{2}\\.\\d{4}$"}
    ]

    template = DocumentTemplate(
        lawyer_id=lawyer.id,
        name="Test",
        file_path="test_template.docx",
        questions=questions
    )
    db_session.add(template)
    await db_session.commit()

    return {"lawyer": lawyer, "client": client, "template": template}

@pytest.mark.asyncio
async def test_document_validation(db_session, setup_data):
    storage = MemoryStorage()

    class MockMessage:
        def __init__(self, text):
            self.text = text
            self.answers = []

        async def answer(self, text, **kwargs):
            self.answers.append(text)

        async def answer_document(self, doc, **kwargs):
            self.answers.append("document sent")

    class MockBot:
        async def send_message(self, *args, **kwargs):
            pass

    class MockState(FSMContext):
        def __init__(self):
            super().__init__(storage=storage, key=None) # type: ignore
            self._data = {
                "template_id": setup_data["template"].id,
                "client_id": setup_data["client"].id,
                "questions": setup_data["template"].questions,
                "current_q_index": 0,
                "answers": {}
            }

        async def get_data(self):
            return self._data

        async def update_data(self, **kwargs):
            self._data.update(kwargs)

        async def clear(self):
            pass

    state = MockState()

    def _(key, **kwargs):
        return key

    # Invalid passport
    msg = MockMessage("12345")
    msg.bot = MockBot() # type: ignore
    await answer_question(msg, state, _, db_session)
    assert "invalid_format" in msg.answers[0]

    # Valid passport
    msg = MockMessage("AA1234567")
    msg.bot = MockBot() # type: ignore
    await answer_question(msg, state, _, db_session)
    assert msg.answers[0] == "Date?"

    # Invalid date
    msg = MockMessage("2023-01-01")
    msg.bot = MockBot() # type: ignore
    await answer_question(msg, state, _, db_session)
    assert "invalid_format" in msg.answers[0]

    # Valid date (completes the flow)
    msg = MockMessage("01.01.2023")
    msg.bot = MockBot() # type: ignore
    await answer_question(msg, state, _, db_session)
    assert "generating_document" in msg.answers[0]
    assert "document sent" in msg.answers[1]

    # Cleanup
    if os.path.exists("test_template.docx"):
        os.remove("test_template.docx")