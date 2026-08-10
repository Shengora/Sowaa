import pytest
import pytest_asyncio
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.app.core.database import Base, get_db
from backend.app.main import app

# Create in-memory SQLite for testing endpoint integration
engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(autouse=True, scope="function")
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

client = TestClient(app)

@pytest.mark.asyncio
async def test_register_and_login(setup_database):
    # Register
    res = client.post("/api/auth/register", json={"email": "test@sowaa.com", "password": "pass"})
    assert res.status_code == 200
    assert res.json()["email"] == "test@sowaa.com"

    # Login
    res = client.post("/api/auth/login", json={"email": "test@sowaa.com", "password": "pass"})
    assert res.status_code == 200
    assert "access_token" in res.json()

@pytest.mark.asyncio
async def test_wallet_funding_and_retrieval(setup_database):
    # Setup user and get token
    client.post("/api/auth/register", json={"email": "wallet@sowaa.com", "password": "pass"})
    res = client.post("/api/auth/login", json={"email": "wallet@sowaa.com", "password": "pass"})
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get empty wallet
    res = client.get("/api/wallet", headers=headers)
    assert res.status_code == 200
    assert Decimal(res.json()["balance"]) == Decimal("0.0")

    # Fund wallet (use string for Decimal strictness)
    res = client.post("/api/wallet/fund", json={"amount": "100.50"}, headers=headers)
    assert res.status_code == 200
    assert Decimal(res.json()["balance"]) == Decimal("100.5")

    # Check transactions
    res = client.get("/api/wallet", headers=headers)
    assert len(res.json()["transactions"]) == 1

@pytest.mark.asyncio
async def test_api_key_management(setup_database):
    client.post("/api/auth/register", json={"email": "api@sowaa.com", "password": "pass"})
    res = client.post("/api/auth/login", json={"email": "api@sowaa.com", "password": "pass"})
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create key
    res = client.post("/api/keys", json={"name": "Test Key"}, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "raw_key" in data
    key_id = data["id"]

    # List keys
    res = client.get("/api/keys", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert "raw_key" not in res.json()[0]  # Raw key should not be in list response

    # Revoke key
    res = client.delete(f"/api/keys/{key_id}", headers=headers)
    assert res.status_code == 204

    # List keys again (should be empty)
    res = client.get("/api/keys", headers=headers)
    assert len(res.json()) == 0

@pytest.mark.asyncio
async def test_admin_endpoints_and_audit(setup_database):
    # Setup admin user
    client.post("/api/auth/register", json={"email": "admin@sowaa.com", "password": "pass"})

    # We must hack the DB to make this user an admin since registration defaults to False
    async with TestingSessionLocal() as session:
        from backend.app.models.auth import User
        from sqlalchemy.future import select
        res = await session.execute(select(User).where(User.email == "admin@sowaa.com"))
        user = res.scalars().first()
        user.is_admin = True
        await session.commit()

    res = client.post("/api/auth/login", json={"email": "admin@sowaa.com", "password": "pass"})
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Update markup
    res = client.post("/api/admin/config/markup", json={"markup_percent": "25.0"}, headers=headers)
    assert res.status_code == 200

    # Check audit logs
    res = client.get("/api/admin/audit-logs", headers=headers)
    assert res.status_code == 200
    logs = res.json()
    assert len(logs) == 1
    assert logs[0]["action"] == "SET_MARKUP"
    assert logs[0]["target_resource"] == "system_config:markup_percent"
