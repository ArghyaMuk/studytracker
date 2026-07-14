"""Shared auth dependencies for downstream microservices.

These extract the authenticated user from X-User-Id/X-User-Role headers
set by the API Gateway after JWT verification.
"""

from fastapi import Header, HTTPException, status


async def get_current_user_id(
    x_user_id: str = Header(None, alias="X-User-Id"),
) -> int:
    """Extract authenticated user ID from gateway-forwarded header."""
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        return int(x_user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identity",
        )


async def require_admin(
    x_user_role: str = Header("student", alias="X-User-Role"),
) -> str:
    """Require admin role from gateway-forwarded header."""
    if x_user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return x_user_role
