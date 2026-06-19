"""

JWT helpers.

JWT payload should be minimal:
- sub = user_id
- exp = expiry timestamp

TODO:
- if we later want refresh tokens, keep this file as the place to add them.
"""

from datetime import datetime, timedelta, timezone
from jose import jwt
from jose.exceptions import JWTError

from app.core.config import settings


def create_access_token(*, user_id: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=settings.JWT_EXPIRES_MINUTES)
    payload = {"sub": user_id, "exp": exp}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def decode_token(token: str) -> dict:
    """Raises JWTError if invalid/expired."""
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
