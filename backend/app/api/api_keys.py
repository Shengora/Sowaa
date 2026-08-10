from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from backend.app.core.database import get_db
from backend.app.api.dependencies import get_current_user
from backend.app.models.auth import User, ApiKey
from backend.app.auth.api_keys import generate_api_key

router = APIRouter(prefix="/api/keys", tags=["api_keys"])

class ApiKeyCreate(BaseModel):
    name: str

class ApiKeyResponse(BaseModel):
    id: int
    name: str
    key_prefix: str
    created_at: datetime
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ApiKeyCreateResponse(ApiKeyResponse):
    raw_key: str  # Only shown once

@router.post("", response_model=ApiKeyCreateResponse)
async def create_api_key(key_data: ApiKeyCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    raw_key, key_prefix, hashed_key = generate_api_key()

    new_key = ApiKey(
        user_id=current_user.id,
        name=key_data.name,
        key_prefix=key_prefix,
        hashed_key=hashed_key
    )

    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)

    response_data = {
        "id": new_key.id,
        "name": new_key.name,
        "key_prefix": new_key.key_prefix,
        "created_at": new_key.created_at,
        "last_used_at": new_key.last_used_at,
        "raw_key": raw_key
    }
    return response_data

@router.get("", response_model=List[ApiKeyResponse])
async def list_api_keys(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ApiKey).where(ApiKey.user_id == current_user.id, ApiKey.revoked_at.is_(None))
    )
    keys = result.scalars().all()
    return keys

@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(key_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == current_user.id))
    key = result.scalars().first()

    if not key or key.revoked_at is not None:
        raise HTTPException(status_code=404, detail="API Key not found or already revoked")

    key.revoked_at = datetime.utcnow()
    await db.commit()
    return
