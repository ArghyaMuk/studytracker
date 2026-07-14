import time
import logging

import redis.asyncio as redis_client
from fastapi import HTTPException, Request, status

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis: redis_client.Redis | None = None


async def _get_redis() -> redis_client.Redis | None:
    global _redis
    if _redis is None:
        try:
            _redis = redis_client.from_url(settings.redis_url, decode_responses=True)
            await _redis.ping()
        except Exception as e:
            logger.warning(f"Redis unavailable for rate limiting: {e}")
            _redis = None
    return _redis


async def check_rate_limit(request: Request, user_id: str | None = None) -> None:
    """Check rate limit using Redis sliding window. Falls back to no-limit if Redis unavailable."""
    if not user_id:
        return

    r = await _get_redis()
    if not r:
        return  # Skip rate limiting if Redis unavailable

    key = f"ratelimit:{user_id}"
    window = settings.rate_limit_window_seconds
    max_requests = settings.rate_limit_requests

    try:
        now = time.time()
        pipe = r.pipeline()
        # Remove old entries
        pipe.zremrangebyscore(key, 0, now - window)
        # Add current request
        pipe.zadd(key, {str(now): now})
        # Count requests in window
        pipe.zcard(key)
        # Set expiry on the key
        pipe.expire(key, window)
        results = await pipe.execute()
        request_count = results[2]

        if request_count > max_requests:
            retry_after = int(window - (now - float((await r.zrange(key, 0, 0))[0])))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(max(1, retry_after))},
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Rate limit check failed: {e}")
        # Fail open — don't block requests if Redis has issues
