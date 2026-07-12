from shared.auth import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)
from .config import settings


def create_tokens(user_id: int, email: str) -> dict[str, str]:
    """Create access and refresh token pair for a user."""
    data = {"sub": str(user_id), "email": email}
    access_token = create_access_token(
        data,
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_minutes=settings.jwt_access_token_expire_minutes,
    )
    refresh_token = create_refresh_token(
        data,
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_days=settings.jwt_refresh_token_expire_days,
    )
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


def decode_token(token: str) -> dict | None:
    return verify_token(token, settings.jwt_secret_key, settings.jwt_algorithm)
