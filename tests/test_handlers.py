import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from aiogram.types import Message, User as AiogramUser, Chat
from aiogram.fsm.context import FSMContext
from bot.database.core import Base
from bot.database.models import User, Lawyer, Client, Role
from bot.handlers.start import start_cmd
import secrets

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session

@pytest_asyncio.fixture
def mock_message():
    class MockMessage:
        def __init__(self, text):
            self.text = text
            self.from_user = AiogramUser(id=123, is_bot=False, first_name="Test")
            self.answers = []

        async def answer(self, text, **kwargs):
            self.answers.append(text)

    return MockMessage

@pytest.mark.asyncio
async def test_start_no_token(mock_message, db_session):
    msg = mock_message("/start")

    def _(key):
        return key

    await start_cmd(msg, _, db_session)
    assert msg.answers[0] == "start_no_token"

@pytest.mark.asyncio
async def test_start_invalid_token(mock_message, db_session):
    msg = mock_message("/start invalid_token")

    def _(key):
        return key

    await start_cmd(msg, _, db_session)
    assert msg.answers[0] == "start_invalid_token"

@pytest.mark.asyncio
async def test_start_valid_token(mock_message, db_session):
    # Create lawyer
    lawyer_user = User(telegram_id=999, role=Role.lawyer)
    db_session.add(lawyer_user)
    await db_session.flush()

    token = secrets.token_urlsafe(16)
    lawyer = Lawyer(user_id=lawyer_user.id, invite_token=token)
    db_session.add(lawyer)
    await db_session.commit()

    msg = mock_message(f"/start {token}")

    def _(key):
        return key

    await start_cmd(msg, _, db_session)
    assert msg.answers[0] == "start_success"