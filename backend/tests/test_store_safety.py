from __future__ import annotations

import pytest
from uuid import UUID

from app.infrastructure.db.models import CurrencyTransactionType
from app.infrastructure.db.session import async_session_maker
from app.modules.economy.repository.wallet_repository import WalletRepository


async def _credit_lumens(user_id: str, amount: int) -> None:
    async with async_session_maker() as session:
        wallet = WalletRepository(session)
        await wallet.adjust_balance(
            user_id=UUID(user_id),
            amount=amount,
            reason=CurrencyTransactionType.manual_adjustment,
            context=f"tests:store:{user_id}:{amount}",
            metadata={"source": "pytest"},
        )
        await session.commit()


async def _register_store_user(async_client, email: str) -> tuple[str, str]:
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "display_name": "Store User",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    me = await async_client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    return token, me.json()["id"]


async def _purchase_store_item(async_client, *, token: str, slug: str, client_token: str) -> dict:
    response = await async_client.post(
        f"/api/v1/store/{slug}/purchase",
        headers={"Authorization": f"Bearer {token}"},
        json={"client_token": client_token},
    )
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.asyncio
async def test_store_list_returns_seeded_items(async_client, unique_email: str):
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "password123",
            "display_name": "Store User",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]

    response = await async_client.get(
        "/api/v1/store",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data


@pytest.mark.asyncio
async def test_store_purchase_rejects_too_long_client_token(async_client, unique_email: str):
    token, _user_id = await _register_store_user(async_client, unique_email)

    response = await async_client.post(
        "/api/v1/store/pro-trial-pass/purchase",
        headers={"Authorization": f"Bearer {token}"},
        json={"client_token": "x" * 81},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_store_exposes_affordable_starter_items_for_user_with_8_lmn(async_client, unique_email: str):
    token, user_id = await _register_store_user(async_client, unique_email)
    await _credit_lumens(user_id, 8)

    response = await async_client.get(
        "/api/v1/store",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    items = response.json()
    affordable_starters = [
        item
        for item in items
        if item["kind"] == "starter" and item["price"] <= 8 and item["is_affordable"] is True
    ]
    assert affordable_starters


@pytest.mark.asyncio
async def test_first_starter_purchase_keeps_loop_alive_with_bonus(async_client, unique_email: str):
    token, user_id = await _register_store_user(async_client, unique_email)
    await _credit_lumens(user_id, 8)

    response = await async_client.post(
        "/api/v1/store/starter-mini-prompt/purchase",
        headers={"Authorization": f"Bearer {token}"},
        json={"client_token": "starter-mini-prompt-001"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["purchase"]["item"]["kind"] == "starter"
    assert body["first_purchase_reward"]["amount"] == 4
    assert body["wallet"]["balance"] == 7
    assert any(item["slug"] == "starter-structure-fragment" for item in body["available_items"])


@pytest.mark.asyncio
async def test_insufficient_funds_error_reports_missing_lmn(async_client, unique_email: str):
    token, user_id = await _register_store_user(async_client, unique_email)
    await _credit_lumens(user_id, 3)

    response = await async_client.post(
        "/api/v1/store/starter-mini-prompt/purchase",
        headers={"Authorization": f"Bearer {token}"},
        json={"client_token": "starter-mini-prompt-low-balance"},
    )

    assert response.status_code == 400, response.text
    body = response.json()
    assert body["code"] == "insufficient_funds"
    assert body["details"]["missing"] == 2


@pytest.mark.asyncio
async def test_store_client_token_is_scoped_per_user(async_client, unique_email: str):
    token_one, user_one = await _register_store_user(async_client, unique_email)
    token_two, user_two = await _register_store_user(async_client, unique_email.replace("@", ".other@"))
    await _credit_lumens(user_one, 50)
    await _credit_lumens(user_two, 50)

    first = await _purchase_store_item(
        async_client,
        token=token_one,
        slug="pro-trial-pass",
        client_token="shared-store-token-001",
    )
    second = await _purchase_store_item(
        async_client,
        token=token_two,
        slug="pro-trial-pass",
        client_token="shared-store-token-001",
    )

    assert first["purchase"]["id"] != second["purchase"]["id"]
