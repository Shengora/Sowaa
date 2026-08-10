from decimal import Decimal
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.core.database import Base

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    balance = Column(Numeric(precision=16, scale=6), default=Decimal("0.0"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="wallet")
    reservations = relationship("WalletReservation", back_populates="wallet")
    transactions = relationship("Transaction", back_populates="wallet")

class WalletReservation(Base):
    __tablename__ = "wallet_reservations"

    id = Column(String, primary_key=True, index=True) # UUID string
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    amount = Column(Numeric(precision=16, scale=6), nullable=False)
    status = Column(String, nullable=False, default="RESERVED") # RESERVED, CAPTURED, RELEASED, FAILED
    created_at = Column(DateTime, default=datetime.utcnow)

    wallet = relationship("Wallet", back_populates="reservations")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    amount = Column(Numeric(precision=16, scale=6), nullable=False)
    transaction_type = Column(String, nullable=False) # DEPOSIT, CHARGE, REFUND
    reference_id = Column(String, nullable=True) # e.g. payment intent ID or request ID
    created_at = Column(DateTime, default=datetime.utcnow)

    wallet = relationship("Wallet", back_populates="transactions")

class Pricing(Base):
    __tablename__ = "pricing"

    id = Column(Integer, primary_key=True, index=True)
    model = Column(String, nullable=False, index=True)
    provider = Column(String, nullable=False)
    input_price = Column(Numeric(precision=16, scale=6), nullable=False)
    output_price = Column(Numeric(precision=16, scale=6), nullable=False)
    currency = Column(String, default="USD")
    effective_from = Column(DateTime, default=datetime.utcnow)
    effective_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
