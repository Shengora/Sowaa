import os

# Set before any bot import
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from bot.database.core import Base

@pytest_asyncio.fixture(scope="session")
def engine():
    return create_async_engine("sqlite+aiosqlite:///:memory:")

@pytest_asyncio.fixture
async def db_session(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session

@pytest_asyncio.fixture
def session_maker(engine):
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
