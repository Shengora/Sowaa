from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

from backend.app.core.database import get_db
from backend.app.api.dependencies import get_current_admin_user
from backend.app.models.auth import User
from backend.app.models.billing import Pricing
from backend.app.models.provider import Provider, ProviderCompliance, ProviderModel, RequestRecord
from backend.app.models.core import SystemConfig, AuditLog
import json

router = APIRouter(prefix="/api/admin", tags=["admin"])

async def log_audit_action(db: AsyncSession, admin_id: int, action: str, target: str, details: str):
    log = AuditLog(user_id=admin_id, action=action, target_resource=target, details=details)
    db.add(log)
    await db.commit()

# --- Audit Logs ---
class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    target_resource: Optional[str]
    details: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(limit: int = 50, offset: int = 0, admin: User = Depends(get_current_admin_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).offset(offset))
    return result.scalars().all()

# --- Config & Markup ---
class ConfigUpdate(BaseModel):
    markup_percent: str # using string for exact Decimal parsing

@router.post("/config/markup")
async def set_markup(config: ConfigUpdate, admin: User = Depends(get_current_admin_user), db: AsyncSession = Depends(get_db)):
    try:
        markup = Decimal(config.markup_percent)
    except:
        raise HTTPException(status_code=400, detail="Invalid decimal format")

    result = await db.execute(select(SystemConfig).where(SystemConfig.key == "markup_percent"))
    sys_config = result.scalars().first()

    if sys_config:
        sys_config.value_numeric = markup
    else:
        sys_config = SystemConfig(key="markup_percent", value_numeric=markup)
        db.add(sys_config)

    await log_audit_action(db, admin.id, "SET_MARKUP", "system_config:markup_percent", json.dumps({"new_markup": str(markup)}))
    return {"message": "Markup updated"}

# --- User Management ---
class UserInfo(BaseModel):
    id: int
    email: str
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/users", response_model=List[UserInfo])
async def list_users(admin: User = Depends(get_current_admin_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()

@router.post("/users/{user_id}/suspend")
async def suspend_user(user_id: int, admin: User = Depends(get_current_admin_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False

    await log_audit_action(db, admin.id, "SUSPEND_USER", f"user:{user_id}", "")
    return {"message": "User suspended"}

# --- Pricing Management ---
class PricingCreate(BaseModel):
    model: str
    provider: str
    input_price: str
    output_price: str

@router.post("/pricing")
async def set_pricing(pricing_data: PricingCreate, admin: User = Depends(get_current_admin_user), db: AsyncSession = Depends(get_db)):
    try:
        ip = Decimal(pricing_data.input_price)
        op = Decimal(pricing_data.output_price)
    except:
        raise HTTPException(status_code=400, detail="Invalid price format")

    new_pricing = Pricing(
        model=pricing_data.model,
        provider=pricing_data.provider,
        input_price=ip,
        output_price=op
    )
    db.add(new_pricing)

    await log_audit_action(db, admin.id, "SET_PRICING", f"model:{pricing_data.model}", json.dumps({"input": str(ip), "output": str(op)}))
    return {"message": "Pricing updated successfully"}

# --- Provider Compliance ---
@router.post("/providers/{provider_name}/compliance")
async def verify_provider_compliance(provider_name: str, admin: User = Depends(get_current_admin_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProviderCompliance).where(ProviderCompliance.provider_name == provider_name))
    compliance = result.scalars().first()

    if not compliance:
        compliance = ProviderCompliance(provider_name=provider_name)
        db.add(compliance)

    compliance.is_verified = True
    compliance.verified_at = datetime.utcnow()
    compliance.verified_by = admin.id

    await log_audit_action(db, admin.id, "VERIFY_PROVIDER_COMPLIANCE", f"provider:{provider_name}", "")
    return {"message": f"Provider {provider_name} marked as compliant"}

# --- Revenue & Health ---
class RevenueResponse(BaseModel):
    total_revenue: Decimal
    total_upstream_cost: Decimal
    total_platform_margin: Decimal

@router.get("/revenue", response_model=RevenueResponse)
async def get_revenue_stats(admin: User = Depends(get_current_admin_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            func.sum(RequestRecord.customer_charge).label("total_revenue"),
            func.sum(RequestRecord.upstream_cost).label("total_upstream_cost"),
            func.sum(RequestRecord.platform_revenue).label("total_platform_margin")
        ).where(RequestRecord.status == "success")
    )
    row = result.first()

    return {
        "total_revenue": row.total_revenue or Decimal("0.0"),
        "total_upstream_cost": row.total_upstream_cost or Decimal("0.0"),
        "total_platform_margin": row.total_platform_margin or Decimal("0.0")
    }

class AdminUsageStatsResponse(BaseModel):
    total_platform_requests: int
    total_platform_tokens: int

@router.get("/usage", response_model=AdminUsageStatsResponse)
async def get_all_usage_stats(admin: User = Depends(get_current_admin_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            func.count(RequestRecord.id).label("total_platform_requests"),
            func.sum(RequestRecord.total_tokens).label("total_platform_tokens")
        )
    )
    row = result.first()
    return {
        "total_platform_requests": row.total_platform_requests or 0,
        "total_platform_tokens": row.total_platform_tokens or 0
    }

@router.get("/requests")
async def get_all_requests(limit: int = 50, offset: int = 0, admin: User = Depends(get_current_admin_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RequestRecord).order_by(RequestRecord.created_at.desc()).limit(limit).offset(offset)
    )
    records = result.scalars().all()
    out = []
    for r in records:
        out.append({
            "id": r.id,
            "user_id": r.user_id,
            "model": r.model,
            "provider": r.upstream_provider,
            "total_tokens": r.total_tokens,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else ""
        })
    return out
