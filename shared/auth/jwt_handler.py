"""
JWT Handler – Shared token creation and verification utilities.

Provides functions to create short-lived access tokens and long-lived refresh
tokens, plus a verification function used by middleware across all services.
Tokens are signed with HMAC-SHA256 (HS256) by default.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt


def create_access_token(
    data: dict[str, Any],
    secret_key: str,
    algorithm: str = "HS256",
    expires_minutes: int = 15,
) -> str:
    """Create a short-lived access token for API authorization.

    The token embeds the provided claims (typically sub, email, role) plus:
    - 'exp': expiration timestamp (now + expires_minutes)
    - 'type': "access" – distinguishes from refresh tokens during verification
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, secret_key, algorithm=algorithm)


def create_refresh_token(
    data: dict[str, Any],
    secret_key: str,
    algorithm: str = "HS256",
    expires_days: int = 7,
) -> str:
    """Create a long-lived refresh token for obtaining new access tokens.

    Same claims as the access token but with a longer TTL (days instead of
    minutes) and 'type' set to "refresh" so the backend can reject refresh
    tokens used in place of access tokens.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=expires_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, secret_key, algorithm=algorithm)


def verify_token(token: str, secret_key: str, algorithm: str = "HS256") -> dict[str, Any] | None:
    """Verify and decode a JWT token.

    Returns the decoded payload dict on success, or None if the token is
    invalid, expired, or tampered with. Callers should treat None as
    "unauthorized".
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        return payload
    except JWTError:
        # Covers expired tokens, bad signatures, malformed JWTs
        return None
