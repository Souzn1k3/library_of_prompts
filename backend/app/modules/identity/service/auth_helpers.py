import hashlib
import secrets
import uuid
from datetime import datetime, timezone


def as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def new_refresh_token_pair() -> tuple[str, str]:
    token_jti = uuid.uuid4().hex
    token = f"{token_jti}.{secrets.token_urlsafe(48)}"
    return token_jti, token
