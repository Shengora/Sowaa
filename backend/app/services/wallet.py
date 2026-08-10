import uuid
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from datetime import datetime

from backend.app.models.billing import Wallet, WalletReservation, Transaction

async def get_wallet_balance(db: AsyncSession, user_id: int) -> Decimal:
    result = await db.execute(select(Wallet).where(Wallet.user_id == user_id))
    wallet = result.scalars().first()
    if not wallet:
        return Decimal('0.0')
    return wallet.balance

async def add_funds(db: AsyncSession, user_id: int, amount: Decimal, reference_id: str = None) -> Wallet:
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    result = await db.execute(select(Wallet).where(Wallet.user_id == user_id).with_for_update())
    wallet = result.scalars().first()

    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    wallet.balance += amount

    transaction = Transaction(
        id=str(uuid.uuid4()),
        wallet_id=wallet.id,
        amount=amount,
        transaction_type="DEPOSIT",
        reference_id=reference_id
    )
    db.add(transaction)

    await db.commit()
    await db.refresh(wallet)
    return wallet

async def reserve_funds(db: AsyncSession, user_id: int, amount: Decimal) -> WalletReservation:
    """Atomically reserves funds. Raises exception if insufficient balance."""
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Reservation amount must be positive")

    result = await db.execute(select(Wallet).where(Wallet.user_id == user_id).with_for_update())
    wallet = result.scalars().first()

    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    if wallet.balance < amount:
        raise HTTPException(status_code=402, detail="Insufficient funds")

    wallet.balance -= amount

    reservation = WalletReservation(
        id=str(uuid.uuid4()),
        wallet_id=wallet.id,
        amount=amount,
        status="RESERVED"
    )
    db.add(reservation)

    await db.commit()
    await db.refresh(reservation)
    return reservation

async def capture_and_refund(db: AsyncSession, reservation_id: str, actual_cost: Decimal, reference_id: str = None) -> None:
    """Captures the actual cost from a reservation and refunds any remainder."""
    if actual_cost < 0:
        raise HTTPException(status_code=400, detail="Actual cost cannot be negative")

    result = await db.execute(select(WalletReservation).where(WalletReservation.id == reservation_id).with_for_update())
    reservation = result.scalars().first()

    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    if reservation.status != "RESERVED":
        raise HTTPException(status_code=400, detail=f"Reservation already processed (status: {reservation.status})")

    if actual_cost > reservation.amount:
        # In a real system, you might want to force a negative balance or just capture what you can.
        # For Sowaa, we capture up to the reserved amount.
        # It's an error if we exceed, but let's cap it at the reservation limit to avoid negative balance.
        actual_cost = reservation.amount

    refund_amount = reservation.amount - actual_cost

    # Get the wallet to apply refund
    result_wallet = await db.execute(select(Wallet).where(Wallet.id == reservation.wallet_id).with_for_update())
    wallet = result_wallet.scalars().first()

    # Create the charge transaction
    if actual_cost > 0:
        charge_tx = Transaction(
            id=str(uuid.uuid4()),
            wallet_id=wallet.id,
            amount=-actual_cost, # negative for charge
            transaction_type="CHARGE",
            reference_id=reference_id
        )
        db.add(charge_tx)

    # Process refund
    if refund_amount > 0:
        wallet.balance += refund_amount
        refund_tx = Transaction(
            id=str(uuid.uuid4()),
            wallet_id=wallet.id,
            amount=refund_amount,
            transaction_type="REFUND",
            reference_id=reference_id
        )
        db.add(refund_tx)

    reservation.status = "CAPTURED"
    await db.commit()

async def release_reservation(db: AsyncSession, reservation_id: str) -> None:
    """Releases a reservation entirely, refunding the full amount."""
    result = await db.execute(select(WalletReservation).where(WalletReservation.id == reservation_id).with_for_update())
    reservation = result.scalars().first()

    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    if reservation.status != "RESERVED":
        raise HTTPException(status_code=400, detail=f"Reservation already processed (status: {reservation.status})")

    # Get wallet
    result_wallet = await db.execute(select(Wallet).where(Wallet.id == reservation.wallet_id).with_for_update())
    wallet = result_wallet.scalars().first()

    wallet.balance += reservation.amount

    refund_tx = Transaction(
        id=str(uuid.uuid4()),
        wallet_id=wallet.id,
        amount=reservation.amount,
        transaction_type="REFUND",
        reference_id=reservation.id
    )
    db.add(refund_tx)

    reservation.status = "RELEASED"
    await db.commit()
