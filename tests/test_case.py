import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from bot.database.core import Base
from bot.database.models import User, Lawyer, Client, Role, Case, CaseStatus
from bot.services.case import CaseService

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session

@pytest.mark.asyncio
async def test_case_isolation(db_session):
    # Create two lawyers and their clients
    l1_user = User(telegram_id=1, role=Role.lawyer)
    l2_user = User(telegram_id=2, role=Role.lawyer)
    db_session.add_all([l1_user, l2_user])
    await db_session.flush()

    l1 = Lawyer(user_id=l1_user.id, invite_token="l1")
    l2 = Lawyer(user_id=l2_user.id, invite_token="l2")
    db_session.add_all([l1, l2])
    await db_session.flush()

    c1_user = User(telegram_id=3, role=Role.client)
    db_session.add(c1_user)
    await db_session.flush()
    c1 = Client(user_id=c1_user.id, lawyer_id=l1.id)
    db_session.add(c1)
    await db_session.flush()

    # Lawyer 1 creates a case
    case = await CaseService.create_case(db_session, "Test case", c1.id, l1.id)
    await db_session.commit()

    # Lawyer 1 can see it
    l1_cases = await CaseService.get_lawyer_cases(db_session, l1.id)
    assert len(l1_cases) == 1
    assert l1_cases[0].id == case.id

    # Lawyer 2 cannot see it
    l2_cases = await CaseService.get_lawyer_cases(db_session, l2.id)
    assert len(l2_cases) == 0

    # Ensure status history exists
    assert case.status == CaseStatus.new