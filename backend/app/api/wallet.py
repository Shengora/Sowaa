from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from decimal import Decimal
from typing import List, Optional
from datetime import datetime

from backend.app.core.database import get_db
from backend.app.api.dependencies import get_current_user
from backend.app.models.auth import User
from backend.app.models.billing import Wallet, Transaction
from backend.app.services.wallet import add_funds

router = APIRouter(prefix="/api/wallet", tags=["wallet"])

class FundWalletRequest(BaseModel):
    amount: str  # Use string to strictly parse into Decimal avoiding float inaccuracy

class TransactionResponse(BaseModel):
    id: str
    amount: Decimal
    transaction_type: str
    created_at: datetime

    class Config:
        from_attributes = True

class WalletResponse(BaseModel):
    balance: Decimal
    transactions: List[TransactionResponse]

    class Config:
        from_attributes = True

@router.get("", response_model=WalletResponse)
async def get_wallet(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Wallet).where(Wallet.user_id == current_user.id))
    wallet = result.scalars().first()

    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    tx_result = await db.execute(
        select(Transaction).where(Transaction.wallet_id == wallet.id).order_by(Transaction.created_at.desc())
    )
    transactions = tx_result.scalars().all()

    return {
        "balance": wallet.balance,
        "transactions": transactions
    }

@router.post("/fund", response_model=WalletResponse)
async def fund_wallet(fund_req: FundWalletRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        amount = Decimal(fund_req.amount)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid amount format")

    if amount <= Decimal("0.0"):
        raise HTTPException(status_code=400, detail="Amount must be positive")

    wallet = await add_funds(db, current_user.id, amount, reference_id="mock_payment")

    # Return updated wallet
    tx_result = await db.execute(
        select(Transaction).where(Transaction.wallet_id == wallet.id).order_by(Transaction.created_at.desc())
    )
    transactions = tx_result.scalars().all()

    return {
        "balance": wallet.balance,
        "transactions": transactions
    }
