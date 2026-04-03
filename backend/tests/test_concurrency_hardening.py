from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, func, select, update

from app.config import get_settings
from app.infrastructure.db.models import (
    AuthRefreshToken,
    Category,
    CurrencyTransaction,
    CurrencyTransactionType,
    LockedRewardStatus,
    ModerationState,
    Plan,
    PlanTier,
    PlanUsageWindow,
    Prompt,
    PromptEntitlement,
    PromptPaymentMethod,
    PromptPrice,
    PromptPurchase,
    PromptStatus,
    PromptTechnique,
    PurchaseStatus,
    StoreItem,
    User,
    UserPurchase,
    UserLockedReward,
)
from app.infrastructure.db.session import async_session_maker
from app.main import create_app
from app.modules.economy.repository.wallet_repository import WalletRepository
from app.modules.marketplace.service.marketplace_service import price_lumens_from_rub


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _billing_window(now: datetime) -> tuple[datetime, datetime]:
    start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    if now.month == 12:
        end = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)
    return start, end


async def _register_user(async_client: AsyncClient, *, email: str, display_name: str) -> dict[str, str]:
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "display_name": display_name,
        },
    )
    assert reg.status_code == 201, reg.text
    token = reg.json()["access_token"]
    me = await async_client.get("/api/v1/users/me", headers=_auth_headers(token))
    assert me.status_code == 200, me.text
    payload = me.json()
    return {"token": token, "id": payload["id"]}


async def _credit_lumens(*, user_id: UUID, amount: int) -> None:
    async with async_session_maker() as session:
        wallet = WalletRepository(session)
        await wallet.adjust_balance(
            user_id=user_id,
            amount=amount,
            reason=CurrencyTransactionType.manual_adjustment,
            context=f"tests:concurrency:{user_id}:{amount}",
            metadata={"source": "pytest"},
        )
        await session.commit()


async def _ensure_category_id() -> UUID:
    async with async_session_maker() as session:
        existing = (
            await session.execute(select(Category).where(Category.slug == "pytest-concurrency-marketplace"))
        ).scalar_one_or_none()
        if existing is not None:
            return existing.id
        category = Category(
            slug="pytest-concurrency-marketplace",
            name="Pytest Concurrency Marketplace",
            sort_order=0,
            is_restricted=False,
        )
        session.add(category)
        await session.flush()
        await session.commit()
        return category.id


async def _create_paid_prompt(
    *,
    author_id: UUID,
    slug: str,
    title: str,
    price_rub: int,
) -> tuple[UUID, str]:
    category_id = await _ensure_category_id()
    async with async_session_maker() as session:
        prompt = Prompt(
            slug=slug,
            title=title,
            body=f"{title} body.\n" * 20,
            summary=f"{title} summary",
            status=PromptStatus.published,
            technique=PromptTechnique.other,
            moderation_state=ModerationState.approved,
            category_id=category_id,
            author_id=author_id,
            is_premium=True,
        )
        session.add(prompt)
        await session.flush()
        session.add(
            PromptPrice(
                prompt_id=prompt.id,
                price_rub=price_rub,
                price_lumens=price_lumens_from_rub(price_rub),
                commission_percent=5,
                is_active=True,
            )
        )
        await session.commit()
        return prompt.id, prompt.slug


@pytest.mark.asyncio
async def test_refresh_token_rotation_concurrent_reuse_does_not_500(async_client: AsyncClient, unique_email: str) -> None:
    user = await _register_user(async_client, email=unique_email, display_name="Refresh Race User")
    user_id = UUID(user["id"])
    settings = get_settings()
    refresh_cookie_name = settings.refresh_token_cookie_name
    refresh_token = async_client.cookies.get(refresh_cookie_name)
    assert refresh_token

    async def _refresh_once() -> tuple[int, dict]:
        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            cookies={refresh_cookie_name: refresh_token},
        ) as client:
            response = await client.post("/api/v1/auth/refresh")
            body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            return response.status_code, body

    results = await asyncio.gather(*[_refresh_once() for _ in range(3)])
    statuses = [status for status, _ in results]

    assert all(status < 500 for status in statuses)
    assert statuses.count(200) == 1
    assert statuses.count(401) == 2
    failure_codes = {body.get("code") for status, body in results if status == 401}
    assert failure_codes <= {"refresh_token_reused", "invalid_refresh_token"}

    async with async_session_maker() as session:
        active_count = int(
            (
                await session.execute(
                    select(func.count())
                    .select_from(AuthRefreshToken)
                    .where(AuthRefreshToken.user_id == user_id, AuthRefreshToken.revoked_at.is_(None))
                )
            ).scalar_one()
            or 0
        )
    assert active_count == 0


@pytest.mark.asyncio
async def test_marketplace_lumen_purchase_concurrent_client_token_dedup(
    async_client: AsyncClient,
    unique_email: str,
) -> None:
    seller = await _register_user(async_client, email=unique_email, display_name="Seller Lumen Race")
    buyer = await _register_user(
        async_client,
        email=unique_email.replace("@", ".buyer@"),
        display_name="Buyer Lumen Race",
    )
    prompt_id, _ = await _create_paid_prompt(
        author_id=UUID(seller["id"]),
        slug="pytest-concurrency-lumen-prompt",
        title="Pytest Concurrency Lumen Prompt",
        price_rub=235,
    )
    buyer_id = UUID(buyer["id"])
    await _credit_lumens(user_id=buyer_id, amount=12_000)

    async def _buy_once() -> int:
        response = await async_client.post(
            f"/api/v1/marketplace/prompts/{prompt_id}/buy-with-lumens",
            headers=_auth_headers(buyer["token"]),
            json={"client_token": "concurrency-lumen-client-token"},
        )
        return response.status_code

    statuses = await asyncio.gather(*[_buy_once() for _ in range(8)])
    assert all(status < 500 for status in statuses)
    assert set(statuses).issubset({200, 409})
    assert any(status == 200 for status in statuses)

    async with async_session_maker() as session:
        purchases = (
            await session.execute(
                select(PromptPurchase).where(
                    PromptPurchase.user_id == buyer_id,
                    PromptPurchase.prompt_id == prompt_id,
                    PromptPurchase.payment_method == PromptPaymentMethod.lumens,
                )
            )
        ).scalars().all()
        completed = [row for row in purchases if row.status == PurchaseStatus.completed]
        assert len(completed) == 1

        active_entitlements = (
            await session.execute(
                select(PromptEntitlement).where(
                    PromptEntitlement.user_id == buyer_id,
                    PromptEntitlement.prompt_id == prompt_id,
                    PromptEntitlement.revoked_at.is_(None),
                )
            )
        ).scalars().all()
        assert len(active_entitlements) == 1


@pytest.mark.asyncio
async def test_marketplace_checkout_concurrent_client_token_idempotency(
    async_client: AsyncClient,
    unique_email: str,
) -> None:
    seller = await _register_user(async_client, email=unique_email, display_name="Seller Checkout Race")
    buyer = await _register_user(
        async_client,
        email=unique_email.replace("@", ".buyer2@"),
        display_name="Buyer Checkout Race",
    )
    prompt_id, _ = await _create_paid_prompt(
        author_id=UUID(seller["id"]),
        slug="pytest-concurrency-checkout-prompt",
        title="Pytest Concurrency Checkout Prompt",
        price_rub=260,
    )
    buyer_id = UUID(buyer["id"])

    async def _checkout_once() -> int:
        response = await async_client.post(
            "/api/v1/marketplace/prompts/checkout-session",
            headers=_auth_headers(buyer["token"]),
            json={"prompt_id": str(prompt_id), "client_token": "concurrency-checkout-client-token"},
        )
        return response.status_code

    statuses = await asyncio.gather(*[_checkout_once() for _ in range(8)])
    assert all(status < 500 for status in statuses)
    assert set(statuses).issubset({200, 409})
    assert any(status == 200 for status in statuses)

    async with async_session_maker() as session:
        purchases = (
            await session.execute(
                select(PromptPurchase).where(
                    PromptPurchase.user_id == buyer_id,
                    PromptPurchase.prompt_id == prompt_id,
                    PromptPurchase.payment_method == PromptPaymentMethod.stripe,
                )
            )
        ).scalars().all()
        assert len(purchases) == 1
        assert purchases[0].status == PurchaseStatus.completed

        entitlements = (
            await session.execute(
                select(PromptEntitlement).where(
                    PromptEntitlement.user_id == buyer_id,
                    PromptEntitlement.prompt_id == prompt_id,
                    PromptEntitlement.revoked_at.is_(None),
                )
            )
        ).scalars().all()
        assert len(entitlements) == 1


@pytest.mark.asyncio
async def test_plan_usage_window_concurrent_auto_unlock_consumes_single_slot(
    async_client: AsyncClient,
    unique_email: str,
) -> None:
    seller = await _register_user(async_client, email=unique_email, display_name="Seller Plan Window")
    buyer = await _register_user(
        async_client,
        email=unique_email.replace("@", ".buyer3@"),
        display_name="Buyer Plan Window",
    )
    prompt_id, slug = await _create_paid_prompt(
        author_id=UUID(seller["id"]),
        slug="pytest-concurrency-plan-window-prompt",
        title="Pytest Concurrency Plan Window Prompt",
        price_rub=240,
    )
    buyer_id = UUID(buyer["id"])
    now = datetime.now(timezone.utc)
    window_start, window_end = _billing_window(now)

    async with async_session_maker() as session:
        await session.execute(
            update(User)
            .where(User.id == buyer_id)
            .values(plan_tier=PlanTier.free, premium_unlock_until=None)
        )
        await session.execute(
            update(Plan)
            .where(Plan.tier == PlanTier.free)
            .values(monthly_paid_prompt_limit=2, prompt_purchase_discount_percent=0, lumen_purchase_discount_percent=0)
        )
        await session.execute(
            delete(PlanUsageWindow).where(
                PlanUsageWindow.user_id == buyer_id,
                PlanUsageWindow.plan_tier == PlanTier.free,
            )
        )
        await session.execute(
            delete(PromptEntitlement).where(
                PromptEntitlement.user_id == buyer_id,
                PromptEntitlement.prompt_id == prompt_id,
            )
        )
        await session.execute(
            delete(PromptPurchase).where(
                PromptPurchase.user_id == buyer_id,
                PromptPurchase.prompt_id == prompt_id,
                PromptPurchase.payment_method == PromptPaymentMethod.included_limit,
            )
        )
        await session.commit()

    async def _open_prompt_once() -> int:
        response = await async_client.get(
            f"/api/v1/prompts/by-slug/{slug}",
            headers=_auth_headers(buyer["token"]),
        )
        return response.status_code

    statuses = await asyncio.gather(*[_open_prompt_once() for _ in range(6)])
    assert all(status == 200 for status in statuses)

    async with async_session_maker() as session:
        windows = (
            await session.execute(
                select(PlanUsageWindow).where(
                    PlanUsageWindow.user_id == buyer_id,
                    PlanUsageWindow.plan_tier == PlanTier.free,
                    PlanUsageWindow.window_started_at == window_start,
                    PlanUsageWindow.window_ends_at == window_end,
                )
            )
        ).scalars().all()
        assert len(windows) == 1
        assert int(windows[0].used_paid_prompt_unlocks) == 1

        purchases = (
            await session.execute(
                select(PromptPurchase).where(
                    PromptPurchase.user_id == buyer_id,
                    PromptPurchase.prompt_id == prompt_id,
                    PromptPurchase.payment_method == PromptPaymentMethod.included_limit,
                    PromptPurchase.status == PurchaseStatus.completed,
                )
            )
        ).scalars().all()
        assert len(purchases) == 1

        entitlements = (
            await session.execute(
                select(PromptEntitlement).where(
                    PromptEntitlement.user_id == buyer_id,
                    PromptEntitlement.prompt_id == prompt_id,
                    PromptEntitlement.revoked_at.is_(None),
                )
            )
        ).scalars().all()
        assert len(entitlements) == 1


@pytest.mark.asyncio
async def test_store_one_time_purchase_concurrent_requests_do_not_duplicate(async_client: AsyncClient, unique_email: str) -> None:
    user = await _register_user(async_client, email=unique_email, display_name="Store One-Time Race")
    user_id = UUID(user["id"])
    await _credit_lumens(user_id=user_id, amount=100)

    async def _purchase_once() -> int:
        response = await async_client.post(
            "/api/v1/store/starter-mini-prompt/purchase",
            headers=_auth_headers(user["token"]),
            json={"client_token": "concurrency-store-one-time-token"},
        )
        return response.status_code

    statuses = await asyncio.gather(*[_purchase_once() for _ in range(8)])
    assert all(status < 500 for status in statuses)
    assert set(statuses).issubset({200, 409})
    assert any(status == 200 for status in statuses)

    async with async_session_maker() as session:
        item = (await session.execute(select(StoreItem).where(StoreItem.slug == "starter-mini-prompt"))).scalar_one()

        completed_rows = (
            await session.execute(
                select(UserPurchase).where(
                    UserPurchase.user_id == user_id,
                    UserPurchase.store_item_id == item.id,
                    UserPurchase.status == PurchaseStatus.completed,
                )
            )
        ).scalars().all()
        assert len(completed_rows) == 1

        debits = (
            await session.execute(
                select(CurrencyTransaction).where(
                    CurrencyTransaction.user_id == user_id,
                    CurrencyTransaction.reason == CurrencyTransactionType.store_purchase,
                    CurrencyTransaction.source_id == item.id,
                )
            )
        ).scalars().all()
        assert len(debits) == 1


@pytest.mark.asyncio
async def test_locked_cashback_unlock_concurrency_grants_once(async_client: AsyncClient, unique_email: str) -> None:
    user = await _register_user(async_client, email=unique_email, display_name="Cashback Unlock Race")
    user_id = UUID(user["id"])
    now = datetime.now(timezone.utc)

    async with async_session_maker() as session:
        wallet = WalletRepository(session)
        reward = await wallet.create_locked_cashback(
            user_id=user_id,
            amount=17,
            source_purchase_id=None,
            unlock_by=now + timedelta(hours=1),
            metadata={"source": "concurrency-test"},
        )
        assert reward is not None
        reward_id = reward.id
        await session.commit()

    gate = asyncio.Event()

    async def _progress_once() -> list[UUID]:
        async with async_session_maker() as session:
            wallet = WalletRepository(session)
            await gate.wait()
            unlocked = await wallet.progress_locked_cashback(user_id=user_id, mission_progress=1, now=now)
            await session.commit()
            return [row.id for row in unlocked]

    tasks = [asyncio.create_task(_progress_once()) for _ in range(3)]
    gate.set()
    await asyncio.gather(*tasks)

    async with async_session_maker() as session:
        reward_row = (
            await session.execute(select(UserLockedReward).where(UserLockedReward.id == reward_id))
        ).scalar_one()
        assert reward_row.status == LockedRewardStatus.unlocked

        unlock_txs = (
            await session.execute(
                select(CurrencyTransaction).where(
                    CurrencyTransaction.user_id == user_id,
                    CurrencyTransaction.reason == CurrencyTransactionType.cashback_unlocked,
                    CurrencyTransaction.source_id == reward_id,
                )
            )
        ).scalars().all()
        assert len(unlock_txs) == 1
