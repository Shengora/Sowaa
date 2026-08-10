import os
import time
import redis.asyncio as redis
from fastapi import HTTPException

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Use a global pool for the application
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

async def check_rate_limit(user_id: int, requests_per_minute: int = 60):
    """
    Basic fixed-window rate limiting using Redis.
    Uses the current minute as part of the key.
    """
    try:
        current_minute = int(time.time() / 60)
        key = f"rate_limit:{user_id}:{current_minute}"

        # Use an atomic pipeline
        async with redis_client.pipeline(transaction=True) as pipe:
            pipe.incr(key)
            pipe.expire(key, 60)
            results = await pipe.execute()

        request_count = results[0]

        if request_count > requests_per_minute:
            raise HTTPException(status_code=429, detail="Too many requests")

    except redis.RedisError:
        # If redis fails, we probably shouldn't block all traffic, but log it.
        # For Sowaa, we'll allow the request if rate limiting is temporarily down,
        # but in strict mode you might block it.
        pass
