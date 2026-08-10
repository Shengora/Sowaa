from typing import Dict, Any, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.models.provider import ProviderModel, Provider, ProviderCompliance
from backend.app.providers.base import BaseProvider
from backend.app.providers.anthropic import AnthropicProvider
from backend.app.providers.mock import MockProvider

def get_provider_instance(provider_name: str) -> BaseProvider:
    if provider_name == "anthropic":
        return AnthropicProvider()
    elif provider_name == "mock":
        return MockProvider()
    else:
        raise HTTPException(status_code=500, detail=f"Unsupported provider: {provider_name}")

async def route_model(db: AsyncSession, requested_model: str) -> Dict[str, Any]:
    """
    Looks up the requested model in the registry and returns routing info.
    Checks that the provider is active and legally compliant.
    """
    # For tests and initial bootstrap, we might allow a direct 'mock' route.
    if requested_model.startswith("mock-"):
        return {
            "provider_name": "mock",
            "upstream_model_id": requested_model,
            "provider_instance": MockProvider()
        }

    result = await db.execute(
        select(ProviderModel, Provider)
        .join(Provider, ProviderModel.provider_id == Provider.id)
        .where(ProviderModel.customer_model_name == requested_model)
        .where(ProviderModel.is_active == True)
        .where(Provider.is_active == True)
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Model not found or unavailable")

    provider_model, provider = row

    # Check compliance
    compliance_result = await db.execute(
        select(ProviderCompliance)
        .where(ProviderCompliance.provider_name == provider.name)
        .where(ProviderCompliance.is_verified == True)
    )
    compliance = compliance_result.scalars().first()

    if not compliance:
        raise HTTPException(status_code=403, detail="Provider not authorized for commercial proxy use")

    provider_instance = get_provider_instance(provider.name)

    return {
        "provider_name": provider.name,
        "upstream_model_id": provider_model.upstream_model_id,
        "provider_instance": provider_instance
    }
