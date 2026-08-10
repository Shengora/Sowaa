from sqlalchemy import Column, String, Integer, DateTime, Numeric
from datetime import datetime
from backend.app.core.database import Base

class SystemConfig(Base):
    """Holds global system configurations like markup percentage."""
    __tablename__ = "system_config"

    key = Column(String, primary_key=True, index=True)
    value_numeric = Column(Numeric(precision=16, scale=6), nullable=True)
    value_string = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuditLog(Base):
    """Immutable log of significant system/admin actions."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True) # Who performed the action
    action = Column(String, nullable=False, index=True) # e.g. "SET_MARKUP", "SUSPEND_USER"
    target_resource = Column(String, nullable=True) # e.g. "user:123"
    details = Column(String, nullable=True) # JSON string or text summary without secrets
    created_at = Column(DateTime, default=datetime.utcnow)
