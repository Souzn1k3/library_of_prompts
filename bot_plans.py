from __future__ import annotations

from datetime import datetime, timezone

SUBSCRIPTION_PERIOD_SECONDS = 30 * 24 * 60 * 60
PLAN_ORDER = ("free", "starter", "pro", "enterprise")
PAID_PLAN_ORDER = ("starter", "pro", "enterprise")

PLAN_METADATA = {
    "free": {
        "badge": "🆓",
        "stars_price_month": 0,
        "ai_daily_limit": 20,
        "max_freezes": 2,
        "coin_bonus_percent": 0,
        "premium_prompts": False,
        "restricted_categories": False,
        "titles": {"ru": "Free", "en": "Free", "tt": "Free"},
    },
    "starter": {
        "badge": "🚀",
        "stars_price_month": 150,
        "ai_daily_limit": 50,
        "max_freezes": 3,
        "coin_bonus_percent": 20,
        "premium_prompts": True,
        "restricted_categories": False,
        "titles": {"ru": "Starter", "en": "Starter", "tt": "Starter"},
    },
    "pro": {
        "badge": "💎",
        "stars_price_month": 750,
        "ai_daily_limit": 150,
        "max_freezes": 5,
        "coin_bonus_percent": 50,
        "premium_prompts": True,
        "restricted_categories": True,
        "titles": {"ru": "Pro", "en": "Pro", "tt": "Pro"},
    },
    "enterprise": {
        "badge": "👑",
        "stars_price_month": 900,
        "ai_daily_limit": 0,
        "max_freezes": 0,
        "coin_bonus_percent": 100,
        "premium_prompts": True,
        "restricted_categories": True,
        "titles": {"ru": "MAX", "en": "MAX", "tt": "MAX"},
    },
}


def normalize_plan_tier(value: str | None) -> str:
    raw = (value or "free").strip().lower()
    if raw in {"max", "enterprise"}:
        return "enterprise"
    if raw in PLAN_METADATA:
        return raw
    return "free"


def get_plan_config(value: str | None) -> dict:
    return PLAN_METADATA[normalize_plan_tier(value)]


def get_plan_title(value: str | None, lang: str = "ru") -> str:
    tier = normalize_plan_tier(value)
    config = get_plan_config(tier)
    return config["titles"].get(lang, config["titles"]["ru"])


def get_plan_badge(value: str | None) -> str:
    return str(get_plan_config(value)["badge"])


def tier_rank(value: str | None) -> int:
    tier = normalize_plan_tier(value)
    return PLAN_ORDER.index(tier)


def has_same_or_higher_plan(current_tier: str | None, target_tier: str | None) -> bool:
    return tier_rank(current_tier) >= tier_rank(target_tier)


def is_paid_tier(value: str | None) -> bool:
    return normalize_plan_tier(value) != "free"


def parse_datetime(value) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return None


def format_expiry(value, lang: str = "ru") -> str | None:
    dt = parse_datetime(value)
    if dt is None:
        return None
    if lang == "en":
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    return dt.strftime("%d.%m.%Y %H:%M UTC")


def build_subscription_payload(user_id: int, tier: str, token: str) -> str:
    normalized = normalize_plan_tier(tier)
    return f"tgsub:{normalized}:{user_id}:{token}"


def parse_subscription_payload(payload: str | None) -> dict | None:
    if not payload:
        return None
    parts = payload.split(":")
    if len(parts) != 4 or parts[0] != "tgsub":
        return None
    _, tier, raw_user_id, token = parts
    if not token:
        return None
    try:
        user_id = int(raw_user_id)
    except ValueError:
        return None
    return {
        "tier": normalize_plan_tier(tier),
        "user_id": user_id,
        "token": token,
        "provider_subscription_id": f"tgstars_{user_id}_{token}",
    }
