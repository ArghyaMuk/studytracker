import time

from fastapi import HTTPException, Request, status

from app.core.config import settings

# In-memory rate limiting (replace with Redis in production)
_rate_store: dict[str, list[float]] = {}


async def check_rate_limit(request: Request, user_id: str | None = None) -> None:
    """Check rate limit for a user. Uses sliding window."""
    if not user_id:
        return

    now = time.time()
    window = settings.rate_limit_window_seconds
    max_requests = settings.rate_limit_requests

    key = f"rate:{user_id}"
    if key not in _rate_store:
        _rate_store[key] = []

    # Remove old entries outside the window
    _rate_store[key] = [ts for ts in _rate_store[key] if now - ts < window]

    if len(_rate_store[key]) >= max_requests:
        retry_after = int(window - (now - _rate_store[key][0]))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(max(1, retry_after))},
        )

    _rate_store[key].append(now)
