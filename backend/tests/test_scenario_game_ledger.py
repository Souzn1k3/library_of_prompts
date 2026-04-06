from __future__ import annotations

import hmac
from datetime import datetime, timezone
from hashlib import sha256

import pytest
from sqlalchemy import func, select

from app.config import get_settings
from app.infrastructure.db.models import CurrencyTransaction, User, UserCurrencyBalance
from app.infrastructure.db.session import async_session_maker

TELEGRAM_HEADERS = {"X-Telegram-Bot-Key": "pytest-telegram-bot-sync-key"}
REWARD_SECRET = "pytest-telegram-reward-signing-secret"


async def _register(async_client, email: str, display_name: str = "Game Ledger User") -> str:
    unique_display_name = f"{display_name}-{email.split('@', 1)[0][-8:]}"
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "supersecret123",
            "display_name": unique_display_name,
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"]


async def _set_telegram_user_id(email: str, telegram_user_id: int) -> None:
    async with async_session_maker() as session:
        user = (await session.execute(select(User).where(User.email == email.lower()))).scalar_one()
        user.telegram_user_id = telegram_user_id
        user.telegram_is_active = True
        await session.commit()


def _tg_signature(*, claim_id: str, telegram_user_id: int, reward_tokens: int, reason: str, challenge_key: str, occurred_at_iso: str) -> str:
    payload = "|".join([claim_id, str(telegram_user_id), str(reward_tokens), reason, challenge_key, occurred_at_iso])
    return hmac.new(REWARD_SECRET.encode("utf-8"), payload.encode("utf-8"), sha256).hexdigest()


@pytest.mark.asyncio
async def test_web_demo_game_valid_earn_and_duplicate_prevention(async_client):
    state = await async_client.get("/api/v1/scenarios/game/state")
    assert state.status_code == 200
    assert state.json()["pending_tokens"] == 0

    earn = await async_client.post(
        "/api/v1/scenarios/game/earn",
        json={
            "event_id": "web-game-event-1",
            "challenge_id": "challenge-1",
            "choice_index": 1,
        },
    )
    assert earn.status_code == 200
    payload = earn.json()
    assert payload["accepted"] is True
    assert payload["reward_tokens"] == 6
    assert payload["pending_tokens"] >= 6

    duplicate = await async_client.post(
        "/api/v1/scenarios/game/earn",
        json={
            "event_id": "web-game-event-1",
            "challenge_id": "challenge-1",
            "choice_index": 1,
        },
    )
    assert duplicate.status_code == 200
    duplicate_payload = duplicate.json()
    assert duplicate_payload["accepted"] is False
    assert duplicate_payload["reason"] == "duplicate_event_id"


@pytest.mark.asyncio
async def test_web_demo_game_cooldown_and_daily_cap(async_client):
    settings = get_settings()
    original_cap = settings.web_demo_game_daily_token_cap
    settings.web_demo_game_daily_token_cap = 6
    try:
        first = await async_client.post(
            "/api/v1/scenarios/game/earn",
            json={
                "event_id": "web-game-cap-1",
                "challenge_id": "challenge-2",
                "choice_index": 1,
            },
        )
        assert first.status_code == 200
        assert first.json()["accepted"] is True
        assert first.json()["daily_cap_remaining"] == 0

        cooldown = await async_client.post(
            "/api/v1/scenarios/game/earn",
            json={
                "event_id": "web-game-cap-2",
                "challenge_id": "challenge-2",
                "choice_index": 0,
            },
        )
        assert cooldown.status_code == 200
        assert cooldown.json()["accepted"] is False
        assert cooldown.json()["reason"] == "challenge_cooldown_active"

        capped = await async_client.post(
            "/api/v1/scenarios/game/earn",
            json={
                "event_id": "web-game-cap-3",
                "challenge_id": "challenge-3",
                "choice_index": 1,
            },
        )
        assert capped.status_code == 200
        assert capped.json()["accepted"] is False
        assert capped.json()["reason"] == "daily_cap_reached"
    finally:
        settings.web_demo_game_daily_token_cap = original_cap


@pytest.mark.asyncio
async def test_web_demo_game_pending_vs_wallet_and_claim(async_client, unique_email: str):
    token = await _register(async_client, unique_email)

    guest_earn = await async_client.post(
        "/api/v1/scenarios/game/earn",
        json={
            "event_id": "web-game-claim-pending-1",
            "challenge_id": "challenge-3",
            "choice_index": 0,
        },
    )
    assert guest_earn.status_code == 200
    assert guest_earn.json()["accepted"] is True

    wallet_before = await async_client.get("/api/v1/wallet", headers={"Authorization": f"Bearer {token}"})
    assert wallet_before.status_code == 200
    before_balance = int(wallet_before.json()["balance"])

    claim = await async_client.post(
        "/api/v1/scenarios/game/claim",
        headers={"Authorization": f"Bearer {token}"},
        json={"claim_id": "web-game-claim-1"},
    )
    assert claim.status_code == 200
    claim_payload = claim.json()
    assert claim_payload["applied"] is True
    assert claim_payload["claimed_tokens"] > 0
    assert claim_payload["pending_tokens_after"] == 0

    wallet_after = await async_client.get("/api/v1/wallet", headers={"Authorization": f"Bearer {token}"})
    assert wallet_after.status_code == 200
    after_balance = int(wallet_after.json()["balance"])
    assert after_balance >= before_balance + int(claim_payload["claimed_tokens"])

    repeat_claim = await async_client.post(
        "/api/v1/scenarios/game/claim",
        headers={"Authorization": f"Bearer {token}"},
        json={"claim_id": "web-game-claim-1"},
    )
    assert repeat_claim.status_code == 200
    assert repeat_claim.json()["claimed_tokens"] == claim_payload["claimed_tokens"]


@pytest.mark.asyncio
async def test_web_demo_game_claim_requires_auth(async_client):
    denied = await async_client.post("/api/v1/scenarios/game/claim", json={"claim_id": "guest-claim-denied"})
    assert denied.status_code == 401


@pytest.mark.asyncio
async def test_web_demo_game_and_tg_rewards_do_not_conflict(async_client, unique_email: str):
    token = await _register(async_client, unique_email)
    await _set_telegram_user_id(unique_email, 99887766)

    web_earn = await async_client.post(
        "/api/v1/scenarios/game/earn",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "event_id": "web-vs-tg-1",
            "challenge_id": "challenge-1",
            "choice_index": 1,
        },
    )
    assert web_earn.status_code == 200
    assert web_earn.json()["accepted"] is True

    web_claim = await async_client.post(
        "/api/v1/scenarios/game/claim",
        headers={"Authorization": f"Bearer {token}"},
        json={"claim_id": "web-vs-tg-claim"},
    )
    assert web_claim.status_code == 200
    assert web_claim.json()["applied"] is True

    occurred_at_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    tg_claim_id = "tg-vs-web-claim-1"
    tg_signature = _tg_signature(
        claim_id=tg_claim_id,
        telegram_user_id=99887766,
        reward_tokens=5,
        reason="token_sprint_win",
        challenge_key="round_conflict",
        occurred_at_iso=occurred_at_iso,
    )
    tg_claim = await async_client.post(
        "/api/v1/telegram/rewards/claim",
        headers=TELEGRAM_HEADERS,
        json={
            "claim_id": tg_claim_id,
            "telegram_user_id": 99887766,
            "reward_tokens": 5,
            "reason": "token_sprint_win",
            "challenge_key": "round_conflict",
            "occurred_at": occurred_at_iso,
            "signature": tg_signature,
        },
    )
    assert tg_claim.status_code == 200
    assert tg_claim.json()["verified"] is True

    async with async_session_maker() as session:
        user = (await session.execute(select(User).where(User.email == unique_email.lower()))).scalar_one()
        balance = (
            await session.execute(
                select(UserCurrencyBalance).where(UserCurrencyBalance.user_id == user.id)
            )
        ).scalar_one_or_none()
        assert balance is not None

        web_tx = (
            await session.execute(
                select(func.count())
                .select_from(CurrencyTransaction)
                .where(
                    CurrencyTransaction.user_id == user.id,
                    CurrencyTransaction.context == "web_demo_claim:web-vs-tg-claim",
                )
            )
        ).scalar_one()
        tg_tx = (
            await session.execute(
                select(func.count())
                .select_from(CurrencyTransaction)
                .where(
                    CurrencyTransaction.user_id == user.id,
                    CurrencyTransaction.context == "tg_reward_claim:tg-vs-web-claim-1",
                )
            )
        ).scalar_one()
        assert int(web_tx or 0) == 1
        assert int(tg_tx or 0) == 1
