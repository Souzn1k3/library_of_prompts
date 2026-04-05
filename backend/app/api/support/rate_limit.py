from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import Request

from app.core.rate_limit import enforce_rate_limit, resolve_rate_limit_ip


@dataclass(frozen=True, slots=True)
class RateLimitRule:
    key_template: str
    limit: int
    window_seconds: int


async def enforce_request_rate_limits(
    request: Request,
    rules: tuple[RateLimitRule, ...],
    *,
    values: dict[str, Any] | None = None,
) -> str:
    ip = resolve_rate_limit_ip(request)
    context: dict[str, Any] = {"ip": ip}
    if values:
        context.update(values)
    for rule in rules:
        key = rule.key_template.format_map(context)
        await enforce_rate_limit(
            key=key,
            limit=rule.limit,
            window_seconds=rule.window_seconds,
        )
    return ip

