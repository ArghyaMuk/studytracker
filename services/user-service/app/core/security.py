"""
Security utilities for the User Service.

Provides convenience wrappers around the shared JWT library to create and
decode token pairs (access + refresh) scoped to a specific user and role.
"""

from shared.auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
)
from .config import settings


def create_tokens(user_id: int, email: str, role: str = "student") -> dict[str, str]:
    """Create an access/refresh token pair for a user.

    The token payload embeds the user's ID (as 'sub'), email, and role so that
    downstream services can authorize requests without a database lookup.
    The role defaults to 'student' but is overridden for admin accounts.
    """
    # Payload claims shared across both tokens
    data = {"sub": str(user_id), "email": email, "role": role}

    # Short-lived access token – used for API authorization
    access_token = create_access_token(
        data,
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_minutes=settings.jwt_access_token_expire_minutes,
    )

    # Long-lived refresh token – used to obtain new access tokens without re-login
    refresh_token = create_refresh_token(
        data,
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_days=settings.jwt_refresh_token_expire_days,
    )

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


def decode_token(token: str) -> dict | None:
    """Decode and verify a JWT. Returns the payload dict or None if invalid/expired."""
    return verify_token(token, settings.jwt_secret_key, settings.jwt_algorithm)
