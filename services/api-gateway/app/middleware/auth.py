from fastapi import Request, HTTPException, status
from shared.auth import verify_token
from app.core.config import settings

# Public endpoints that don't require JWT
PUBLIC_PATHS = {
    "/api/v1/auth/register",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/health",
    "/ready",
    "/docs",
    "/openapi.json",
}


async def verify_jwt_middleware(request: Request) -> dict | None:
    """Verify JWT and return user payload. Returns None for public paths."""
    path = request.url.path

    # Skip auth for public paths
    if path in PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
        return None

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
        )

    token = auth_header.split(" ", 1)[1]
    payload = verify_token(token, settings.jwt_secret_key, settings.jwt_algorithm)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return payload
