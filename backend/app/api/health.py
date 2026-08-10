from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.app.core.database import get_db
from backend.app.middleware.rate_limit import redis_client

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check():
    return {"status": "ok"}

@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    status = {"db": "down", "redis": "down"}

    # Check DB
    try:
        await db.execute(text("SELECT 1"))
        status["db"] = "up"
    except:
        pass

    # Check Redis
    try:
        if await redis_client.ping():
            status["redis"] = "up"
    except:
        pass

    return status
