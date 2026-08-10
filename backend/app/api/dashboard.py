from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal

from backend.app.core.database import get_db
from backend.app.api.dependencies import get_current_user
from backend.app.models.auth import User
from backend.app.models.provider import RequestRecord
from backend.app.models.billing import Wallet

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

class UsageStatsResponse(BaseModel):
    total_requests: int
    total_cost: Decimal
    total_tokens: int

@router.get("/usage", response_model=UsageStatsResponse)
async def get_usage_stats(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            func.count(RequestRecord.id).label("total_requests"),
            func.sum(RequestRecord.customer_charge).label("total_cost"),
            func.sum(RequestRecord.total_tokens).label("total_tokens")
        ).where(RequestRecord.user_id == current_user.id)
    )
    row = result.first()

    return {
        "total_requests": row.total_requests or 0,
        "total_cost": row.total_cost or Decimal("0.0"),
        "total_tokens": row.total_tokens or 0
    }

class RequestHistoryResponse(BaseModel):
    id: str
    model: str
    total_tokens: int
    customer_charge: Decimal
    status: str
    created_at: str

    class Config:
        from_attributes = True

@router.get("/requests", response_model=List[RequestHistoryResponse])
async def get_request_history(
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(RequestRecord)
        .where(RequestRecord.user_id == current_user.id)
        .order_by(RequestRecord.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    records = result.scalars().all()

    # Format the datetimes to strings
    out = []
    for r in records:
        out.append({
            "id": r.id,
            "model": r.model,
            "total_tokens": r.total_tokens,
            "customer_charge": r.customer_charge,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else ""
        })
    return out
