from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import Optional

from backend.app.core.database import get_db
from backend.app.models.auth import User
from backend.app.models.billing import Wallet
from backend.app.auth.utils import get_password_hash, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

class UserCreate(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: int
    email: str
    is_admin: bool

    class Config:
        from_attributes = True

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if user exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user_data.password)

    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        # First user is admin for demo/bootstrap purposes (optional logic, kept false by default)
        is_admin=False
    )
    db.add(new_user)
    await db.flush() # flush to get the user ID

    # Create an initial empty wallet for the customer
    new_wallet = Wallet(user_id=new_user.id, balance=Decimal("0.0"))
    db.add(new_wallet)

    await db.commit()
    await db.refresh(new_user)

    return new_user

class UserLogin(BaseModel):
    email: str
    password: str

@router.post("/login", response_model=Token)
async def login_user(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    from backend.app.auth.utils import verify_password

    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalars().first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.id), "email": user.email, "is_admin": user.is_admin})
    return {"access_token": access_token, "token_type": "bearer"}
