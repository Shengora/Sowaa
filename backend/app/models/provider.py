from decimal import Decimal
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.core.database import Base

class Provider(Base):
    __tablename__ = "upstream_providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ProviderCompliance(Base):
    __tablename__ = "provider_compliance"

    id = Column(Integer, primary_key=True, index=True)
    provider_name = Column(String, unique=True, index=True, nullable=False)
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(String, nullable=True)

class ProviderModel(Base):
    __tablename__ = "provider_models"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("upstream_providers.id"), nullable=False)
    customer_model_name = Column(String, index=True, nullable=False)
    upstream_model_id = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

class RequestRecord(Base):
    __tablename__ = "requests"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=True)
    model = Column(String, nullable=False)
    upstream_provider = Column(String, nullable=False)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    upstream_cost = Column(Numeric(precision=16, scale=6), default=Decimal("0.0"))
    customer_charge = Column(Numeric(precision=16, scale=6), default=Decimal("0.0"))
    platform_revenue = Column(Numeric(precision=16, scale=6), default=Decimal("0.0"))
    latency = Column(Numeric(precision=10, scale=4), nullable=True)
    status = Column(String, nullable=False)
    error_code = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
