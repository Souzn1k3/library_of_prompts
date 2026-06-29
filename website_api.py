import logging
import os
import asyncio
from typing import Any, Dict, List, Optional

import aiohttp
from dotenv import load_dotenv

load_dotenv()

LOGGER = logging.getLogger(__name__)
WEBSITE_API_URL = os.getenv("WEBSITE_API_URL", "https://prompts-vault.ru").rstrip("/")
WEBSITE_BOT_API_KEY = os.getenv("WEBSITE_BOT_API_KEY", "")
API_PREFIX = "/api-proxy/api/v1/telegram"
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=10)
REQUEST_RETRIES = 3
MAX_WEBSITE_CHARGE_ID_LENGTH = 128


def _headers() -> Dict[str, str]:
    """
    Возвращает словарь HTTP-заголовков для запросов к API сайта.

    Если задан WEBSITE_BOT_API_KEY, добавляет заголовок X-Telegram-Bot-Key
    для аутентификации бота на стороне сайта.

    Возвращает:
        Dict[str, str]: Заголовки (Content-Type + опционально API-ключ).
    """
    headers = {"Content-Type": "application/json"}
    if WEBSITE_BOT_API_KEY:
        headers["X-Telegram-Bot-Key"] = WEBSITE_BOT_API_KEY
    return headers


def _url(path: str) -> str:
    """
    Собирает полный URL для запроса к API сайта.

    Аргументы:
        path (str): Относительный путь (например, '/users/upsert').

    Возвращает:
        str: Полный URL вида {WEBSITE_API_URL}{API_PREFIX}{path}.
    """
    return f"{WEBSITE_API_URL}{API_PREFIX}{path}"


def _limit_website_text(value: Optional[str], max_length: int = MAX_WEBSITE_CHARGE_ID_LENGTH) -> Optional[str]:
    """Обрезает строковые поля до лимита текущего API сайта."""
    if value is None:
        return None
    return str(value)[:max_length]


async def _request_json(
    method: str,
    path: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> Optional[Any]:
    """
    Внутренняя утилита: выполняет HTTP-запрос к API сайта и возвращает JSON-ответ.

    Содержит логику повторных попыток (REQUEST_RETRIES) с экспоненциальной задержкой.
    При 4xx/5xx ошибках логирует предупреждение и возвращает None.
    При отсутствии WEBSITE_BOT_API_KEY сразу возвращает None.

    Аргументы:
        method (str): HTTP-метод (GET, POST, DELETE и т.д.).
        path (str): Относительный путь API.
        params (Optional[Dict[str, Any]]): Query-параметры URL.
        payload (Optional[Dict[str, Any]]): Тело запроса (JSON).

    Возвращает:
        Optional[Any]: Распарсенный JSON-ответ или None при ошибке.
    """
    if not WEBSITE_BOT_API_KEY:
        LOGGER.warning("website_api: WEBSITE_BOT_API_KEY is not configured")
        return None

    for attempt in range(REQUEST_RETRIES):
        try:
            async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
                async with session.request(
                    method,
                    _url(path),
                    params=params,
                    json=payload,
                    headers=_headers(),
                ) as response:
                    if response.status >= 500 and attempt + 1 < REQUEST_RETRIES:
                        await asyncio.sleep(1 + attempt)
                        continue
                    if response.status >= 400:
                        body = await response.text()
                        LOGGER.warning(
                            "website_api %s %s failed with status %s: %s",
                            method,
                            path,
                            response.status,
                            body[:300],
                        )
                        return None
                    if response.content_type == "application/json":
                        return await response.json()
                    return None
        except Exception as exc:
            if attempt + 1 >= REQUEST_RETRIES:
                LOGGER.warning("website_api %s %s error: %s", method, path, exc)
                return None
            await asyncio.sleep(1 + attempt)
    return None


async def _request_ok(
    method: str,
    path: str,
    *,
    payload: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Внутренняя утилита: выполняет HTTP-запрос и возвращает True/False в зависимости от успеха.

    Аналог _request_json, но не возвращает тело ответа — только булев флаг.
    Считает успешными статусы 200, 201, 204.

    Аргументы:
        method (str): HTTP-метод.
        path (str): Относительный путь API.
        payload (Optional[Dict[str, Any]]): Тело запроса (JSON).

    Возвращает:
        bool: True если статус ответа 200/201/204, иначе False.
    """
    if not WEBSITE_BOT_API_KEY:
        LOGGER.warning("website_api: WEBSITE_BOT_API_KEY is not configured")
        return False

    for attempt in range(REQUEST_RETRIES):
        try:
            async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
                async with session.request(
                    method,
                    _url(path),
                    json=payload,
                    headers=_headers(),
                ) as response:
                    if response.status in {200, 201, 204}:
                        return True
                    if response.status >= 500 and attempt + 1 < REQUEST_RETRIES:
                        await asyncio.sleep(1 + attempt)
                        continue
                    body = await response.text()
                    LOGGER.warning(
                        "website_api %s %s failed with status %s: %s",
                        method,
                        path,
                        response.status,
                        body[:300],
                    )
                    return False
        except Exception as exc:
            if attempt + 1 >= REQUEST_RETRIES:
                LOGGER.warning("website_api %s %s error: %s", method, path, exc)
                return False
            await asyncio.sleep(1 + attempt)
    return False


async def upsert_user(
    telegram_user_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    language: str = "ru",
) -> Dict[str, Any]:
    """
    Создаёт или обновляет пользователя на сайте (upsert).

    Отправляет POST-запрос на /users/upsert с данными пользователя.
    Если пользователь уже существует — обновляет поля, если нет — создаёт.

    Аргументы:
        telegram_user_id (int): Telegram ID пользователя.
        username (Optional[str]): Username в Telegram.
        first_name (Optional[str]): Имя.
        last_name (Optional[str]): Фамилия.
        language (str): Код языка (по умолчанию 'ru').

    Возвращает:
        Dict[str, Any]: Ответ API (данные пользователя) или пустой словарь при ошибке.
    """
    result = await _request_json(
        "POST",
        "/users/upsert",
        payload={
            "telegram_user_id": telegram_user_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "language": language,
            "is_active": True,
        },
    )
    return result if isinstance(result, dict) else {}


async def get_prompts(
    subcategory_key: str,
    language: str,
    telegram_user_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Получает список промптов для указанной подкатегории.

    GET-запрос к /subcategories/{subcategory_key}/prompts.
    Если передан telegram_user_id — учитывает статус подписки пользователя
    (возвращает полные промпты только для подписчиков).

    Аргументы:
        subcategory_key (str): Ключ подкатегории.
        language (str): Код языка для фильтрации промптов.
        telegram_user_id (Optional[int]): ID пользователя для проверки подписки.

    Возвращает:
        List[Dict[str, Any]]: Список промптов или пустой список при ошибке.
    """
    params: Dict[str, Any] = {"language": language}
    if telegram_user_id:
        params["telegram_user_id"] = telegram_user_id
    result = await _request_json("GET", f"/subcategories/{subcategory_key}/prompts", params=params)
    return result if isinstance(result, list) else []


async def get_saved_prompts(telegram_user_id: int) -> List[Dict[str, Any]]:
    """
    Получает список сохранённых (избранных) промптов пользователя.

    Аргументы:
        telegram_user_id (int): Telegram ID пользователя.

    Возвращает:
        List[Dict[str, Any]]: Список сохранённых промптов или пустой список при ошибке.
    """
    result = await _request_json("GET", f"/users/{telegram_user_id}/saved-prompts")
    return result if isinstance(result, list) else []


async def save_prompt(telegram_user_id: int, prompt_id: str) -> bool:
    """
    Сохраняет промпт в избранное пользователя.

    Аргументы:
        telegram_user_id (int): Telegram ID пользователя.
        prompt_id (str): UUID промпта на сайте.

    Возвращает:
        bool: True если успешно сохранено, иначе False.
    """
    return await _request_ok("POST", f"/users/{telegram_user_id}/saved-prompts/{prompt_id}")


async def delete_saved_prompt(telegram_user_id: int, prompt_id: str) -> bool:
    """
    Удаляет промпт из избранного пользователя.

    Аргументы:
        telegram_user_id (int): Telegram ID пользователя.
        prompt_id (str): UUID промпта на сайте.

    Возвращает:
        bool: True если успешно удалено, иначе False.
    """
    return await _request_ok("DELETE", f"/users/{telegram_user_id}/saved-prompts/{prompt_id}")


async def get_subscription_status(telegram_user_id: int) -> Dict[str, Any]:
    """
    Получает статус подписки пользователя с сайта.

    Аргументы:
        telegram_user_id (int): Telegram ID пользователя.

    Возвращает:
        Dict[str, Any]: Данные о подписке (tier, дата окончания и т.д.)
                        или пустой словарь при ошибке.
    """
    result = await _request_json("GET", f"/users/{telegram_user_id}/subscription")
    return result if isinstance(result, dict) else {}


async def activate_stars_subscription(
    *,
    telegram_user_id: int,
    tier: str,
    provider_subscription_id: str,
    invoice_payload: str,
    telegram_payment_charge_id: str,
    provider_payment_charge_id: Optional[str],
    currency: str,
    total_amount: int,
    current_period_end: Optional[str] = None,
    occurred_at: Optional[str] = None,
    is_recurring: bool = False,
    is_first_recurring: bool = False,
) -> Dict[str, Any]:
    """
    Активирует подписку, купленную за Telegram Stars.

    Отправляет POST-запрос на /subscriptions/activate с данными
    о платеже и подписке. Вызывается после успешной оплаты через Telegram Payments.

    Аргументы:
        telegram_user_id (int): ID пользователя в Telegram.
        tier (str): Тариф подписки (например, 'monthly').
        provider_subscription_id (str): ID подписки от Telegram.
        invoice_payload (str): Payload инвойса (для верификации).
        telegram_payment_charge_id (str): ID платежа от Telegram.
        provider_payment_charge_id (Optional[str]): ID платежа от провайдера.
        currency (str): Валюта (например, 'XTR' для Stars).
        total_amount (int): Сумма платежа в минимальных единицах.
        current_period_end (Optional[str]): Дата окончания текущего периода (ISO).
        occurred_at (Optional[str]): Дата/время платежа (ISO).
        is_recurring (bool): Это рекуррентный платёж?
        is_first_recurring (bool): Это первый рекуррентный платёж?

    Возвращает:
        Dict[str, Any]: Данные активированной подписки или пустой словарь при ошибке.
    """
    payload: Dict[str, Any] = {
        "telegram_user_id": telegram_user_id,
        "tier": tier,
        "provider_subscription_id": provider_subscription_id,
        "invoice_payload": invoice_payload,
        "telegram_payment_charge_id": _limit_website_text(telegram_payment_charge_id),
        "provider_payment_charge_id": _limit_website_text(provider_payment_charge_id),
        "currency": currency,
        "total_amount": total_amount,
        "is_recurring": is_recurring,
        "is_first_recurring": is_first_recurring,
    }
    if current_period_end:
        payload["current_period_end"] = current_period_end
    if occurred_at:
        payload["occurred_at"] = occurred_at

    result = await _request_json("POST", "/subscriptions/activate", payload=payload)
    return result if isinstance(result, dict) else {}


async def get_moderation_queue(
    *,
    acting_telegram_user_id: int,
    skip: int = 0,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Получает очередь промптов на модерацию с сайта.

    Аргументы:
        acting_telegram_user_id (int): ID модератора (для проверки прав).
        skip (int): Смещение для пагинации.
        limit (int): Лимит количества записей (по умолчанию 20).

    Возвращает:
        List[Dict[str, Any]]: Список промптов, ожидающих модерации,
                              или пустой список при ошибке.
    """
    result = await _request_json(
        "GET",
        "/moderation/queue",
        params={
            "acting_telegram_user_id": acting_telegram_user_id,
            "skip": skip,
            "limit": limit,
        },
    )
    return result if isinstance(result, list) else []


async def get_moderation_prompt(
    prompt_id: str,
    *,
    acting_telegram_user_id: int,
) -> Dict[str, Any]:
    """
    Получает детальную информацию о конкретном промпте на модерации.

    Аргументы:
        prompt_id (str): UUID промпта.
        acting_telegram_user_id (int): ID модератора (для проверки прав).

    Возвращает:
        Dict[str, Any]: Данные промпта или пустой словарь при ошибке.
    """
    result = await _request_json(
        "GET",
        f"/moderation/prompts/{prompt_id}",
        params={"acting_telegram_user_id": acting_telegram_user_id},
    )
    return result if isinstance(result, dict) else {}


async def moderate_prompt(
    prompt_id: str,
    *,
    acting_telegram_user_id: int,
    action: str,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Принимает решение по модерации промпта (одобрить / отклонить).

    POST-запрос на /moderation/prompts/{prompt_id}/decision.
    Может быть вызван только модератором.

    Аргументы:
        prompt_id (str): UUID промпта.
        acting_telegram_user_id (int): ID модератора.
        action (str): Действие ('approve' или 'reject').
        reason (Optional[str]): Причина отклонения (обязательна при reject).

    Возвращает:
        Dict[str, Any]: Результат модерации или пустой словарь при ошибке.
    """
    payload: Dict[str, Any] = {
        "acting_telegram_user_id": acting_telegram_user_id,
        "action": action,
    }
    if reason is not None:
        payload["reason"] = reason
    result = await _request_json(
        "POST",
        f"/moderation/prompts/{prompt_id}/decision",
        payload=payload,
    )
    return result if isinstance(result, dict) else {}
