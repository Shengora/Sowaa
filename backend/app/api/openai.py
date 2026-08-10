import os
import uuid
import json
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Dict, Any

from backend.app.core.database import get_db
from backend.app.api.dependencies import get_user_from_api_key
from backend.app.models.auth import User
from backend.app.models.provider import ProviderModel
from backend.app.routing.registry import route_model
from backend.app.middleware.rate_limit import check_rate_limit
from backend.app.services.wallet import reserve_funds, capture_and_refund, release_reservation
from backend.app.services.metering import get_model_pricing, estimate_max_cost, record_usage, get_platform_markup
from backend.app.providers.base import CompletionRequest

router = APIRouter(prefix="/v1", tags=["openai"])

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

@router.get("/models")
async def list_models(user: User = Depends(get_user_from_api_key), db: AsyncSession = Depends(get_db)):
    """Returns available models."""
    result = await db.execute(select(ProviderModel).where(ProviderModel.is_active == True))
    models = result.scalars().all()

    model_list = [{"id": m.customer_model_name, "object": "model", "owned_by": "sowaa"} for m in models]

    # Always include mock for testing
    model_list.append({"id": "mock-model", "object": "model", "owned_by": "sowaa"})

    return {"object": "list", "data": model_list}

@router.post("/chat/completions")
async def chat_completions(
    request: CompletionRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_user_from_api_key),
    db: AsyncSession = Depends(get_db)
):
    await check_rate_limit(user.id)

    request_id = f"req-{uuid.uuid4()}"

    # 1. Route Model
    route_info = await route_model(db, request.model)
    provider_name = route_info["provider_name"]
    upstream_model_id = route_info["upstream_model_id"]
    provider_instance = route_info["provider_instance"]

    request.model = upstream_model_id # Swap to upstream ID

    api_key = ANTHROPIC_API_KEY if provider_name == "anthropic" else "mock-key"

    # 2. Get Pricing, Markup & Reserve Wallet
    markup_decimal = await get_platform_markup(db)

    if provider_name == "mock":
        from backend.app.models.billing import Pricing
        pricing = Pricing(model=upstream_model_id, provider="mock", input_price=Decimal("1.0"), output_price=Decimal("2.0"))
    else:
        pricing = await get_model_pricing(db, upstream_model_id, provider_name)

    estimated_cost = estimate_max_cost(pricing, markup_decimal, request.max_tokens)

    reservation = await reserve_funds(db, user.id, estimated_cost)

    # 3. Handle Streaming vs Non-Streaming
    if request.stream:
        async def stream_generator():
            try:
                # We can't capture final usage until the stream ends
                usage_stats = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

                async for chunk in provider_instance.stream_chat_completion(request, api_key):
                    # In a real app we'd parse the chunk to extract usage if the provider sends it
                    yield chunk

                    if chunk.startswith("data: ") and "[DONE]" not in chunk:
                        try:
                            data = json.loads(chunk[6:])
                            if "usage" in data:
                                usage_stats = data["usage"]
                        except:
                            pass

                actual_cost, _ = await record_usage(
                    db, request_id, user.id, None, upstream_model_id, provider_name, usage_stats, pricing, markup_decimal
                )
                await capture_and_refund(db, reservation.id, actual_cost, request_id)

            except Exception as e:
                # Refund on error
                await release_reservation(db, reservation.id)
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")

    else:
        try:
            response = await provider_instance.chat_completion(request, api_key)
            usage = response.get("usage", {})

            actual_cost, _ = await record_usage(
                db, request_id, user.id, None, upstream_model_id, provider_name, usage, pricing, markup_decimal
            )

            await capture_and_refund(db, reservation.id, actual_cost, request_id)
            return response

        except Exception as e:
            await release_reservation(db, reservation.id)
            raise e
