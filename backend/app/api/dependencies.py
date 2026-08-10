from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional

from backend.app.core.database import get_db
from backend.app.auth.utils import decode_access_token
from backend.app.models.auth import User, ApiKey
from fastapi.security.api_key import APIKeyHeader

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalars().first()

    if user is None or not user.is_active:
        raise credentials_exception

    return user

async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

async def get_user_from_api_key(api_key: str = Depends(api_key_header), db: AsyncSession = Depends(get_db)) -> User:
    import hashlib

    if not api_key:
        raise HTTPException(status_code=401, detail="API Key missing")

    # Remove 'Bearer ' prefix if present
    if api_key.startswith("Bearer "):
        api_key = api_key[7:]

    hashed_key = hashlib.sha256(api_key.encode()).hexdigest()

    result = await db.execute(select(ApiKey).where(ApiKey.hashed_key == hashed_key))
    db_api_key = result.scalars().first()

    if not db_api_key or db_api_key.revoked_at is not None:
        raise HTTPException(status_code=401, detail="Invalid or revoked API Key")

    from datetime import datetime
    db_api_key.last_used_at = datetime.utcnow()
    await db.commit()

    result = await db.execute(select(User).where(User.id == db_api_key.user_id))
    user = result.scalars().first()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User inactive or deleted")

    return user
