import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from aiogram.fsm.storage.memory import MemoryStorage
from bot.database.core import Base
from bot.database.models import User, Lawyer, Client, Role, Subscription
from datetime import datetime, timedelta

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session

@pytest.mark.asyncio
async def test_admin_config_parsing():
    from bot.config import Settings
    settings = Settings(admin_ids="123, 456")
    assert settings.parsed_admin_ids == [123, 456]

@pytest.mark.asyncio
async def test_subscription_middleware(db_session):
    from bot.middlewares.subscription import SubscriptionMiddleware

    class MockMessage:
        def __init__(self, text):
            self.text = text
            self.answers = []

        async def answer(self, text, **kwargs):
            self.answers.append(text)

    # Valid Sub
    user = User(telegram_id=1, role=Role.lawyer)
    db_session.add(user)
    await db_session.flush()
    lawyer = Lawyer(user_id=user.id, invite_token="1")
    db_session.add(lawyer)
    await db_session.flush()
    sub = Subscription(lawyer_id=lawyer.id, active_until=datetime.utcnow() + timedelta(days=1))
    db_session.add(sub)
    await db_session.commit()

    mw = SubscriptionMiddleware()

    async def dummy_handler(event, data):
        return "ok"

    def _(key):
        return key

    msg = MockMessage("/lawyer")
    msg.text = "/lawyer" # Mock text
    # we need to simulate isinstance(event, Message) since middleware checks it
    from aiogram.types import Message
    class DummyMessage(Message):
        def __init__(self):
            super().__init__(message_id=1, date=datetime.utcnow(), chat=None)
            self.text = "/lawyer"
            self.answers = []
        async def answer(self, text, **kwargs):
            self.answers.append(text)

    # Actually, pydantic strictly validates Message, let's just make it simple
    # The middleware uses event.text and event.data, let's patch isinstance
    import bot.middlewares.subscription
    bot.middlewares.subscription.Message = MockMessage

    msg = MockMessage("/lawyer")
    res = await mw(dummy_handler, msg, {"db_user": user, "_": _, "session": db_session})
    assert res == "ok"
    assert len(msg.answers) == 0

    # Expired Sub
    sub.active_until = datetime.utcnow() - timedelta(days=1)
    db_session.add(sub)
    await db_session.commit()

    msg2 = MockMessage("/lawyer")
    res2 = await mw(dummy_handler, msg2, {"db_user": user, "_": _, "session": db_session})
    assert res2 is None
    assert msg2.answers[0] == "subscription_expired"

    # Admin is not blocked (even if role is lawyer but admin bypass not needed because only lawyers are restricted)
    # Wait, the prompt asked to ensure admin is not blocked by subscription.
    # The current middleware logic is `if db_user and db_user.role.value == "lawyer":`
    # Admins have `role = Role.admin`, so they are naturally not blocked.
    admin_user = User(telegram_id=2, role=Role.admin)
    db_session.add(admin_user)
    await db_session.commit()

    msg_admin = MockMessage("/lawyer")
    res_admin = await mw(dummy_handler, msg_admin, {"db_user": admin_user, "_": _, "session": db_session})
    assert res_admin == "ok"
    assert len(msg_admin.answers) == 0
