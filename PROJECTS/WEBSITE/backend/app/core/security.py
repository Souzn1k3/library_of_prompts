from datetime import datetime, timedelta, timezone
import uuid
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(*, subject_user_id: UUID, extra_claims: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode: dict[str, Any] = {
        "sub": str(subject_user_id),
        "exp": expire,
        "typ": "access",
        "jti": uuid.uuid4().hex,
    }
    if extra_claims:
        to_encode.update(extra_claims)
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def parse_user_id_from_token(token: str) -> UUID:
    try:
        payload = decode_token(token)
        token_type = payload.get("typ")
        if token_type not in (None, "access"):
            raise JWTError("unexpected token type")
        sub = payload.get("sub")
        if not sub:
            raise JWTError("missing sub")
        return UUID(str(sub))
    except (JWTError, ValueError) as e:
        raise ValueError("invalid token") from e
