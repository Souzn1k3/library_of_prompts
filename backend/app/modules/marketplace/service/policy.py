from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from app.core.errors import AppError


MARKETPLACE_COMMISSION_PERCENT = 5
LUMEN_PRICE_MULTIPLIER = 4
MIN_PROMPT_PRICE_RUB = 49
MAX_PROMPT_PRICE_RUB = 4999
SETTLEMENT_HOLD_DAYS = 7
REVIEW_EDIT_COOLDOWN_MINUTES = 15
MAX_REVIEW_EDITS = 6
REVIEW_HIDE_REPORT_THRESHOLD = 3
MAX_AUTHOR_REVIEWS_PER_24H = 8
SUSPICIOUS_SELLER_REVIEW_THRESHOLD = 3
ALLOWED_PAYOUT_CURRENCIES = frozenset({"RUB", "LMN"})


def price_lumens_from_rub(price_rub: int) -> int:
    return max(120, int(price_rub) * LUMEN_PRICE_MULTIPLIER)


def normalize_prompt_price(price_rub: int | None) -> tuple[int, int] | None:
    if price_rub is None or price_rub <= 0:
        return None
    if price_rub < MIN_PROMPT_PRICE_RUB or price_rub > MAX_PROMPT_PRICE_RUB:
        raise AppError(
            code="invalid_prompt_price",
            message=f"Prompt price must be between {MIN_PROMPT_PRICE_RUB} and {MAX_PROMPT_PRICE_RUB} RUB.",
            status_code=400,
            details={
                "minimum_price_rub": MIN_PROMPT_PRICE_RUB,
                "maximum_price_rub": MAX_PROMPT_PRICE_RUB,
            },
        )
    return int(price_rub), price_lumens_from_rub(int(price_rub))


def round_rating(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value) + 1e-8, 1)


def fee(amount: int) -> int:
    if amount <= 0:
        return 0
    return max(1, int(math.ceil(amount * (MARKETPLACE_COMMISSION_PERCENT / 100.0))))


def apply_discount(amount: int, discount_percent: int) -> int:
    if amount <= 0 or discount_percent <= 0:
        return amount
    return max(1, int(round(amount * (100 - discount_percent) / 100.0)))


def ensure_aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def start_of_current_month(now: datetime) -> tuple[datetime, datetime]:
    start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    if now.month == 12:
        end = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)
    return start, end


def settlement_available_at(completed_at: datetime | None) -> datetime | None:
    if completed_at is None:
        return None
    return completed_at + timedelta(days=SETTLEMENT_HOLD_DAYS)


def append_query(url: str, **params: str) -> str:
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.update({k: v for k, v in params.items() if v})
    encoded = urlencode(query)
    return urlunparse(parsed._replace(query=encoded))
