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


def _headers() -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if WEBSITE_BOT_API_KEY:
        headers["X-Telegram-Bot-Key"] = WEBSITE_BOT_API_KEY
    return headers


def _url(path: str) -> str:
    return f"{WEBSITE_API_URL}{API_PREFIX}{path}"


async def _request_json(
    method: str,
    path: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> Optional[Any]:
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
    params: Dict[str, Any] = {"language": language}
    if telegram_user_id:
        params["telegram_user_id"] = telegram_user_id
    result = await _request_json("GET", f"/subcategories/{subcategory_key}/prompts", params=params)
    return result if isinstance(result, list) else []


async def get_saved_prompts(telegram_user_id: int) -> List[Dict[str, Any]]:
    result = await _request_json("GET", f"/users/{telegram_user_id}/saved-prompts")
    return result if isinstance(result, list) else []


async def save_prompt(telegram_user_id: int, prompt_id: str) -> bool:
    return await _request_ok("POST", f"/users/{telegram_user_id}/saved-prompts/{prompt_id}")


async def delete_saved_prompt(telegram_user_id: int, prompt_id: str) -> bool:
    return await _request_ok("DELETE", f"/users/{telegram_user_id}/saved-prompts/{prompt_id}")


async def get_subscription_status(telegram_user_id: int) -> Dict[str, Any]:
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
    payload: Dict[str, Any] = {
        "telegram_user_id": telegram_user_id,
        "tier": tier,
        "provider_subscription_id": provider_subscription_id,
        "invoice_payload": invoice_payload,
        "telegram_payment_charge_id": telegram_payment_charge_id,
        "provider_payment_charge_id": provider_payment_charge_id,
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
