import os
from decimal import Decimal
from typing import Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException

from backend.app.models.billing import Pricing
from backend.app.models.provider import RequestRecord
from backend.app.models.core import SystemConfig

async def get_platform_markup(db: AsyncSession) -> Decimal:
    """Dynamically fetches the platform markup from the database."""
    result = await db.execute(select(SystemConfig).where(SystemConfig.key == "markup_percent"))
    config = result.scalars().first()

    if config and config.value_numeric is not None:
        return config.value_numeric / Decimal("100")

    # Fallback to environment variable if not in DB yet
    env_markup = os.getenv("PLATFORM_MARKUP_PERCENT", "20")
    return Decimal(env_markup) / Decimal("100")

async def get_model_pricing(db: AsyncSession, model_name: str, provider_name: str) -> Pricing:
    """Fetches the active pricing for a model."""
    result = await db.execute(
        select(Pricing)
        .where(Pricing.model == model_name)
        .where(Pricing.provider == provider_name)
        .order_by(Pricing.created_at.desc())
    )
    pricing = result.scalars().first()

    if not pricing:
        raise HTTPException(status_code=500, detail=f"No pricing configured for {model_name} on {provider_name}")

    return pricing

def calculate_costs(input_tokens: int, output_tokens: int, pricing: Pricing, markup_decimal: Decimal) -> Tuple[Decimal, Decimal, Decimal]:
    """
    Calculates upstream cost, customer charge, and platform margin.
    Prices are defined per 1M tokens. All calculations use exact Decimal math.
    """
    input_cost = (Decimal(input_tokens) / Decimal("1000000")) * pricing.input_price
    output_cost = (Decimal(output_tokens) / Decimal("1000000")) * pricing.output_price

    upstream_cost = input_cost + output_cost

    # Apply markup
    customer_charge = upstream_cost * (Decimal("1") + markup_decimal)
    platform_revenue = customer_charge - upstream_cost

    return upstream_cost, customer_charge, platform_revenue

async def record_usage(db: AsyncSession, request_id: str, user_id: int, api_key_id: int,
                       model: str, provider: str, usage: Dict[str, int],
                       pricing: Pricing, markup_decimal: Decimal, status: str = "success", error_code: str = None) -> Tuple[Decimal, RequestRecord]:

    input_tokens = usage.get("prompt_tokens", 0)
    output_tokens = usage.get("completion_tokens", 0)
    total_tokens = usage.get("total_tokens", input_tokens + output_tokens)

    upstream_cost, customer_charge, platform_revenue = calculate_costs(input_tokens, output_tokens, pricing, markup_decimal)

    record = RequestRecord(
        id=request_id,
        user_id=user_id,
        api_key_id=api_key_id,
        model=model,
        upstream_provider=provider,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        upstream_cost=upstream_cost,
        customer_charge=customer_charge,
        platform_revenue=platform_revenue,
        status=status,
        error_code=error_code
    )
    db.add(record)
    await db.commit()

    return customer_charge, record

def estimate_max_cost(pricing: Pricing, markup_decimal: Decimal, max_tokens: int = 4000) -> Decimal:
    """
    Estimates the maximum possible cost for a request to reserve wallet funds.
    Assumes standard prompt size (e.g. 1000) + max_tokens output.
    """
    # Conservative estimate: 4k input + max_tokens output
    return calculate_costs(4000, max_tokens, pricing, markup_decimal)[1]
