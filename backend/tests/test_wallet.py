import pytest
import asyncio
import pytest_asyncio
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.app.core.database import Base
from backend.app.models.auth import User
from backend.app.models.billing import Wallet, WalletReservation, Transaction
from backend.app.services.wallet import reserve_funds, add_funds

@pytest_asyncio.fixture
async def db_session():
    # Setup sqlite in-memory for testing logic without Docker postgres
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.mark.asyncio
async def test_wallet_reservation_success(db_session):
    # Setup user and wallet
    user = User(email="test@example.com", hashed_password="pw")
    db_session.add(user)
    await db_session.flush()

    wallet = Wallet(user_id=user.id, balance=Decimal("10.00"))
    db_session.add(wallet)
    await db_session.commit()

    # Reserve 2.00
    res = await reserve_funds(db_session, user.id, Decimal("2.00"))

    # Check balance
    assert wallet.balance == Decimal("8.00")
    assert res.amount == Decimal("2.00")
    assert res.status == "RESERVED"

@pytest.mark.asyncio
async def test_wallet_reservation_insufficient_funds(db_session):
    user = User(email="test2@example.com", hashed_password="pw")
    db_session.add(user)
    await db_session.flush()

    wallet = Wallet(user_id=user.id, balance=Decimal("5.00"))
    db_session.add(wallet)
    await db_session.commit()

    # Try to reserve 10.00
    with pytest.raises(HTTPException) as exc_info:
        await reserve_funds(db_session, user.id, Decimal("10.00"))

    assert exc_info.value.status_code == 402
    assert exc_info.value.detail == "Insufficient funds"

    # Balance unchanged
    assert wallet.balance == Decimal("5.00")

@pytest.mark.asyncio
async def test_wallet_reservation_concurrency(db_session):
    # Setup user and wallet
    user = User(email="concurrent@example.com", hashed_password="pw")
    db_session.add(user)
    await db_session.flush()

    wallet = Wallet(user_id=user.id, balance=Decimal("10.00"))
    db_session.add(wallet)
    await db_session.commit()

    # We will simulate concurrent requests.
    # Note: SQLite in-memory with async engines often struggles with true concurrent row locking
    # without returning 'database is locked'.
    # To prove safety, we verify that only 1 reservation succeeds if they both try to drain the wallet,
    # or that the math remains perfectly correct.

    async def try_reserve(amount_str):
        try:
            return await reserve_funds(db_session, user.id, Decimal(amount_str))
        except HTTPException as e:
            return e

    # Both try to reserve 8.00 from a 10.00 wallet. Only one should succeed.
    results = await asyncio.gather(
        try_reserve("8.00"),
        try_reserve("8.00"),
        return_exceptions=True
    )

    successes = [r for r in results if isinstance(r, WalletReservation)]
    failures = [r for r in results if isinstance(r, HTTPException)]

    assert len(successes) == 1
    assert successes[0].amount == Decimal("8.00")

    assert len(failures) == 1
    assert failures[0].status_code == 402

    # Final balance should be exactly 2.00
    await db_session.refresh(wallet)
    assert wallet.balance == Decimal("2.00")
