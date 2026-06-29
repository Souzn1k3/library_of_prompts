from __future__ import annotations

from datetime import datetime, timezone

# Период подписки в секундах (30 дней)
SUBSCRIPTION_PERIOD_SECONDS = 30 * 24 * 60 * 60
# Все тарифы по возрастанию
PLAN_ORDER = ("free", "starter", "pro", "enterprise")
# Только платные тарифы
PAID_PLAN_ORDER = ("starter", "pro", "enterprise")

# Фичи, добавляемые каждым тарифом (кумулятивно — наследуются от более дешёвых)
PLAN_FEATURES = {
    "free": (
        "free_prompts",
        "premium_prompt_access",
        "basic_lessons",
        "basic_games",
        "streak",
        "tokens",
    ),
    "starter": (
        "intermediate_lessons",
        "prompt_packs_study",
        "saved_prompts",
    ),
    "pro": (
        "complex_prompts",
        "file_prompt_analysis",
        "priority_moderation",
        "prompt_history",
        "pro_badge",
        "improved_prompt_analysis",
        "restricted_categories",
    ),
    "enterprise": (
        "extended_ai_access",
        "best_prompt_analysis",
        "all_categories",
        "all_lessons",
        "max_moderation_priority",
        "author_badge",
        "author_best_prompts",
        "early_access",
        "author_private_tasks",
        "max_private_chat",
        "weekly_top_authors",
        "closed_features",
    ),
}

# Числовые лимиты для каждого тарифа (0 = безлимит)
PLAN_LIMITS = {
    "free": {
        "premium_prompts_monthly": 4,
        "ai_prompt_analysis_daily": 10,
        "moderation_submissions_weekly": 1,
        "streak_freezes": 2,
        "game_coin_bonus_pct": 0,
        "moderation_priority": 0,
        "game_plays_daily": 1,
    },
    "starter": {
        "premium_prompts_monthly": 15,
        "ai_prompt_analysis_daily": 25,
        "moderation_submissions_weekly": 5,
        "streak_freezes": 4,
        "game_coin_bonus_pct": 20,
        "moderation_priority": 0,
        "game_plays_daily": 3,
    },
    "pro": {
        "premium_prompts_monthly": 30,
        "ai_prompt_analysis_daily": 80,
        "moderation_submissions_weekly": 15,
        "streak_freezes": 5,
        "game_coin_bonus_pct": 50,
        "moderation_priority": 10,
        "game_plays_daily": 6,
    },
    "enterprise": {
        "premium_prompts_monthly": 60,
        "ai_prompt_analysis_daily": 160,
        "moderation_submissions_weekly": 30,
        "streak_freezes": 7,
        "game_coin_bonus_pct": 100,
        "moderation_priority": 20,
        "game_plays_daily": 12,
    },
}

# Соответствие между лимитами и периодами их сброса
USAGE_LIMIT_PERIODS = {
    "premium_prompts_monthly": "monthly",
    "ai_prompt_analysis_daily": "daily",
    "moderation_submissions_weekly": "weekly",
    "game_play_ai_quiz": "daily",
    "game_play_prompt_puzzle": "daily",
    "game_play_prompt_battle": "daily",
}

# Алиасы для обратной совместимости: старые имена → канонические имена
LIMIT_ALIASES = {
    "ai_daily_limit": "ai_prompt_analysis_daily",
    "max_freezes": "streak_freezes",
    "coin_bonus_percent": "game_coin_bonus_pct",
}

# Полная мета-информация по каждому тарифу: бейдж, цена, лимиты, фичи, заголовки
PLAN_METADATA = {
    "free": {
        "badge": "🆓",
        "stars_price_month": 0,
        "ai_daily_limit": PLAN_LIMITS["free"]["ai_prompt_analysis_daily"],
        "max_freezes": PLAN_LIMITS["free"]["streak_freezes"],
        "coin_bonus_percent": PLAN_LIMITS["free"]["game_coin_bonus_pct"],
        "premium_prompts": False,
        "restricted_categories": False,
        "features": PLAN_FEATURES["free"],
        "limits": PLAN_LIMITS["free"],
        "titles": {"ru": "Free", "en": "Free", "tt": "Free"},
    },
    "starter": {
        "badge": "🚀",
        "stars_price_month": 100,
        "ai_daily_limit": PLAN_LIMITS["starter"]["ai_prompt_analysis_daily"],
        "max_freezes": PLAN_LIMITS["starter"]["streak_freezes"],
        "coin_bonus_percent": PLAN_LIMITS["starter"]["game_coin_bonus_pct"],
        "premium_prompts": True,
        "restricted_categories": False,
        "features": PLAN_FEATURES["starter"],
        "limits": PLAN_LIMITS["starter"],
        "titles": {"ru": "Starter", "en": "Starter", "tt": "Starter"},
    },
    "pro": {
        "badge": "💎",
        "stars_price_month": 200,
        "ai_daily_limit": PLAN_LIMITS["pro"]["ai_prompt_analysis_daily"],
        "max_freezes": PLAN_LIMITS["pro"]["streak_freezes"],
        "coin_bonus_percent": PLAN_LIMITS["pro"]["game_coin_bonus_pct"],
        "premium_prompts": True,
        "restricted_categories": True,
        "features": PLAN_FEATURES["pro"],
        "limits": PLAN_LIMITS["pro"],
        "titles": {"ru": "Pro", "en": "Pro", "tt": "Pro"},
    },
    "enterprise": {
        "badge": "👑",
        "stars_price_month": 400,
        "ai_daily_limit": PLAN_LIMITS["enterprise"]["ai_prompt_analysis_daily"],
        "max_freezes": PLAN_LIMITS["enterprise"]["streak_freezes"],
        "coin_bonus_percent": PLAN_LIMITS["enterprise"]["game_coin_bonus_pct"],
        "premium_prompts": True,
        "restricted_categories": True,
        "features": PLAN_FEATURES["enterprise"],
        "limits": PLAN_LIMITS["enterprise"],
        "titles": {"ru": "MAX", "en": "MAX", "tt": "MAX"},
    },
}


def normalize_plan_tier(value: str | None) -> str:
    """
    Приводит название тарифа к каноническому виду.

    'max' → 'enterprise', остальные проверяет по PLAN_METADATA,
    при отсутствии — возвращает 'free'.

    Аргументы:
        value (str | None): Сырой тариф (например, 'Pro', 'MAX', None).

    Возвращает:
        str: Нормализованное имя тарифа ('free', 'starter', 'pro', 'enterprise').
    """
    raw = (value or "free").strip().lower()
    if raw in {"max", "enterprise"}:
        return "enterprise"
    if raw in PLAN_METADATA:
        return raw
    return "free"


def get_plan_config(value: str | None) -> dict:
    """
    Возвращает полную конфигурацию тарифа из PLAN_METADATA.

    Аргументы:
        value (str | None): Название тарифа.

    Возвращает:
        dict: Метаданные тарифа (бейдж, цена, лимиты, фичи, заголовки).
    """
    return PLAN_METADATA[normalize_plan_tier(value)]


def _normalize_limit_name(limit_name: str) -> str:
    """
    Преобразует алиас лимита в каноническое имя.

    Например: 'ai_daily_limit' → 'ai_prompt_analysis_daily'.

    Аргументы:
        limit_name (str): Алиас или каноническое имя.

    Возвращает:
        str: Каноническое имя лимита.
    """
    return LIMIT_ALIASES.get(limit_name, limit_name)


def get_plan_features(value: str | None) -> set[str]:
    """
    Собирает все фичи, доступные на данном тарифе и ниже (кумулятивно).

    Аргументы:
        value (str | None): Название тарифа.

    Возвращает:
        set[str]: Набор названий фич (например, 'free_prompts', 'saved_prompts').
    """
    tier = normalize_plan_tier(value)
    features: set[str] = set()
    for candidate in PLAN_ORDER[: tier_rank(tier) + 1]:
        features.update(PLAN_FEATURES.get(candidate, ()))
    return features


def has_plan_feature(value: str | None, feature_name: str) -> bool:
    """
    Проверяет, есть ли у тарифа указанная фича.

    Аргументы:
        value (str | None): Название тарифа.
        feature_name (str): Код фичи (например, 'saved_prompts').

    Возвращает:
        bool: True если фича доступна на этом тарифе или ниже.
    """
    return feature_name in get_plan_features(value)


def get_plan_limits(value: str | None) -> dict[str, int]:
    """
    Возвращает копию словаря лимитов для указанного тарифа.

    Аргументы:
        value (str | None): Название тарифа.

    Возвращает:
        dict[str, int]: Лимиты (ежедневные AI-запросы, заморозки и т.д.).
    """
    tier = normalize_plan_tier(value)
    return dict(PLAN_LIMITS[tier])


def get_plan_limit(value: str | None, limit_name: str) -> int:
    """
    Возвращает значение конкретного лимита для тарифа.

    Аргументы:
        value (str | None): Название тарифа.
        limit_name (str): Имя или алиас лимита.

    Возвращает:
        int: Значение лимита (0 = безлимит).
    """
    normalized = _normalize_limit_name(limit_name)
    return int(get_plan_limits(value).get(normalized, 0))


def get_usage_period(limit_name: str) -> str | None:
    """
    Возвращает период сброса для указанного лимита.

    Аргументы:
        limit_name (str): Имя лимита.

    Возвращает:
        str | None: 'daily', 'weekly', 'monthly' или None.
    """
    return USAGE_LIMIT_PERIODS.get(_normalize_limit_name(limit_name))


def get_feature_min_tier(feature_name: str) -> str | None:
    """
    Находит минимальный тариф, на котором появляется указанная фича.

    Аргументы:
        feature_name (str): Код фичи.

    Возвращает:
        str | None: Название тарифа ('free', 'starter', ...) или None.
    """
    for tier in PLAN_ORDER:
        if feature_name in get_plan_features(tier):
            return tier
    return None


def get_next_plan_for_limit(current_tier: str | None, limit_name: str) -> str | None:
    """
    Находит следующий тариф, где указанный лимит больше (или становится безлимитным).

    Аргументы:
        current_tier (str | None): Текущий тариф.
        limit_name (str): Имя лимита.

    Возвращает:
        str | None: Название следующего тарифа или None, если улучшить нельзя.
    """
    normalized = _normalize_limit_name(limit_name)
    tier = normalize_plan_tier(current_tier)
    current_limit = get_plan_limit(tier, normalized)
    for candidate in PLAN_ORDER[tier_rank(tier) + 1 :]:
        candidate_limit = get_plan_limit(candidate, normalized)
        if current_limit != 0 and (candidate_limit == 0 or candidate_limit > current_limit):
            return candidate
    return None


def get_plan_title(value: str | None, lang: str = "ru") -> str:
    """
    Возвращает локализованное название тарифа.

    Аргументы:
        value (str | None): Название тарифа.
        lang (str): Код языка ('ru', 'en', 'tt').

    Возвращает:
        str: Название тарифа на указанном языке (например, 'Pro').
    """
    tier = normalize_plan_tier(value)
    config = get_plan_config(tier)
    return config["titles"].get(lang, config["titles"]["ru"])


def get_plan_badge(value: str | None) -> str:
    """
    Возвращает эмодзи-бейдж тарифа.

    Аргументы:
        value (str | None): Название тарифа.

    Возвращает:
        str: Эмодзи (например, '🆓', '🚀', '💎', '👑').
    """
    return str(get_plan_config(value)["badge"])


def tier_rank(value: str | None) -> int:
    """
    Возвращает числовой ранг тарифа (0 = free, 1 = starter, ...).

    Аргументы:
        value (str | None): Название тарифа.

    Возвращает:
        int: Индекс в PLAN_ORDER.
    """
    tier = normalize_plan_tier(value)
    return PLAN_ORDER.index(tier)


def has_same_or_higher_plan(current_tier: str | None, target_tier: str | None) -> bool:
    """
    Проверяет, что текущий тариф не ниже target_tier.

    Аргументы:
        current_tier (str | None): Текущий тариф.
        target_tier (str | None): Целевой тариф для сравнения.

    Возвращает:
        bool: True если current >= target.
    """
    return tier_rank(current_tier) >= tier_rank(target_tier)


def is_paid_tier(value: str | None) -> bool:
    """
    Проверяет, является ли тариф платным (не free).

    Аргументы:
        value (str | None): Название тарифа.

    Возвращает:
        bool: True если тариф платный.
    """
    return normalize_plan_tier(value) != "free"


def parse_datetime(value) -> datetime | None:
    """
    Парсит дату/время из различных форматов (datetime, строка ISO, None).

    Приводит к timezone-naive UTC.

    Аргументы:
        value: Объект datetime, строка ISO8601, None.

    Возвращает:
        datetime | None: UTC datetime без таймзоны, или None при пустом значении.
    """
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
    """
    Форматирует дату окончания подписки для отображения пользователю.

    Аргументы:
        value: Дата (datetime, строка, None).
        lang (str): Код языка ('ru' → 'ДД.ММ.ГГГГ ЧЧ:ММ UTC', 'en' → 'ГГГГ-ММ-ДД ЧЧ:ММ UTC').

    Возвращает:
        str | None: Отформатированная строка или None.
    """
    dt = parse_datetime(value)
    if dt is None:
        return None
    if lang == "en":
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    return dt.strftime("%d.%m.%Y %H:%M UTC")


def build_subscription_payload(user_id: int, tier: str, token: str) -> str:
    """
    Формирует payload для инвойса Telegram Stars.

    Формат: 'tgsub:{tier}:{user_id}:{token}'.

    Аргументы:
        user_id (int): Telegram ID пользователя.
        tier (str): Тариф.
        token (str): Уникальный токен для верификации.

    Возвращает:
        str: Строка payload.
    """
    normalized = normalize_plan_tier(tier)
    return f"tgsub:{normalized}:{user_id}:{token}"


def parse_subscription_payload(payload: str | None) -> dict | None:
    """
    Разбирает payload инвойса обратно в структуру.

    Обратная операция к build_subscription_payload.
    Проверяет формат 'tgsub:{tier}:{user_id}:{token}'.

    Аргументы:
        payload (str | None): Строка payload из инвойса.

    Возвращает:
        dict | None: Словарь с ключами tier, user_id, token, provider_subscription_id
                     или None при невалидном формате.
    """
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
