from __future__ import annotations

import hmac
from datetime import datetime, timezone
from hashlib import sha256

import pytest
from sqlalchemy import func, select

from app.infrastructure.db.models import CurrencyTransaction, UserCurrencyBalance
from app.infrastructure.db.session import async_session_maker

TELEGRAM_HEADERS = {"X-Telegram-Bot-Key": "pytest-telegram-bot-sync-key"}
REWARD_SECRET = "pytest-telegram-reward-signing-secret"


def _claim_signature(*, claim_id: str, telegram_user_id: int, reward_tokens: int, reason: str, challenge_key: str, occurred_at_iso: str) -> str:
    payload = "|".join([claim_id, str(telegram_user_id), str(reward_tokens), reason, challenge_key, occurred_at_iso])
    return hmac.new(REWARD_SECRET.encode("utf-8"), payload.encode("utf-8"), sha256).hexdigest()


@pytest.mark.asyncio
async def test_telegram_reward_claim_is_verified_and_idempotent(async_client):
    upsert = await async_client.post(
        "/api/v1/telegram/users/upsert",
        headers=TELEGRAM_HEADERS,
        json={
            "telegram_user_id": 88111,
            "username": "reward_user",
            "first_name": "Reward",
            "language": "ru",
            "is_active": True,
        },
    )
    assert upsert.status_code == 200

    claim_id = "tg-claim-proof-1"
    occurred_at = datetime.now(timezone.utc).replace(microsecond=0)
    occurred_at_iso = occurred_at.isoformat()
    signature = _claim_signature(
        claim_id=claim_id,
        telegram_user_id=88111,
        reward_tokens=9,
        reason="token_sprint_win",
        challenge_key="round_3",
        occurred_at_iso=occurred_at_iso,
    )

    claim_response = await async_client.post(
        "/api/v1/telegram/rewards/claim",
        headers=TELEGRAM_HEADERS,
        json={
            "claim_id": claim_id,
            "telegram_user_id": 88111,
            "reward_tokens": 9,
            "reason": "token_sprint_win",
            "challenge_key": "round_3",
            "occurred_at": occurred_at_iso,
            "signature": signature,
        },
    )
    assert claim_response.status_code == 200
    payload = claim_response.json()
    assert payload["verified"] is True
    assert payload["applied"] is True
    assert payload["balance_after"] is not None

    second_claim = await async_client.post(
        "/api/v1/telegram/rewards/claim",
        headers=TELEGRAM_HEADERS,
        json={
            "claim_id": claim_id,
            "telegram_user_id": 88111,
            "reward_tokens": 9,
            "reason": "token_sprint_win",
            "challenge_key": "round_3",
            "occurred_at": occurred_at_iso,
            "signature": signature,
        },
    )
    assert second_claim.status_code == 200
    second_payload = second_claim.json()
    assert second_payload["verified"] is True
    assert second_payload["applied"] is True
    assert second_payload["balance_after"] == payload["balance_after"]

    async with async_session_maker() as session:
        balance_row = (
            await session.execute(
                select(UserCurrencyBalance).where(
                    UserCurrencyBalance.user_id == select(UserCurrencyBalance.user_id)
                    .join(CurrencyTransaction, CurrencyTransaction.user_id == UserCurrencyBalance.user_id)
                    .where(CurrencyTransaction.context == f"tg_reward_claim:{claim_id}")
                    .scalar_subquery()
                )
            )
        ).scalar_one_or_none()
        assert balance_row is not None

        tx_count = (
            await session.execute(
                select(func.count())
                .select_from(CurrencyTransaction)
                .where(CurrencyTransaction.context == f"tg_reward_claim:{claim_id}")
            )
        ).scalar_one()
        assert int(tx_count or 0) == 1


@pytest.mark.asyncio
async def test_telegram_reward_claim_rejects_invalid_signature(async_client):
    upsert = await async_client.post(
        "/api/v1/telegram/users/upsert",
        headers=TELEGRAM_HEADERS,
        json={
            "telegram_user_id": 88112,
            "username": "invalid_reward_user",
            "first_name": "Invalid",
            "language": "ru",
            "is_active": True,
        },
    )
    assert upsert.status_code == 200

    claim_response = await async_client.post(
        "/api/v1/telegram/rewards/claim",
        headers=TELEGRAM_HEADERS,
        json={
            "claim_id": "tg-claim-proof-invalid",
            "telegram_user_id": 88112,
            "reward_tokens": 7,
            "reason": "token_sprint_win",
            "challenge_key": "round_2",
            "occurred_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "signature": "not-a-valid-signature",
        },
    )
    assert claim_response.status_code == 200
    payload = claim_response.json()
    assert payload["verified"] is False
    assert payload["applied"] is False
    assert payload["verification_error"] == "invalid_signature"
