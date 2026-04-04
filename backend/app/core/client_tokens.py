from __future__ import annotations

import secrets
import uuid
from hashlib import sha256


def scoped_client_token(user_id: uuid.UUID, raw_token: str, *, prefix: str) -> str:
    digest = sha256(raw_token.encode("utf-8")).hexdigest()[:32]
    return f"{prefix}:{user_id.hex}:{digest}"[:80]


def scoped_or_random_token(user_id: uuid.UUID, client_token: str | None, *, prefix: str) -> str:
    raw = (client_token or "").strip()
    if raw:
        return scoped_client_token(user_id, raw, prefix=prefix)
    return f"{prefix}:{user_id.hex}:{secrets.token_hex(8)}"[:80]


def candidate_scoped_tokens(user_id: uuid.UUID, client_token: str, *, prefix: str) -> list[str]:
    raw = client_token.strip()
    if not raw:
        return []
    scoped = scoped_client_token(user_id, raw, prefix=prefix)
    if scoped == raw:
        return [scoped]
    return [scoped, raw]
