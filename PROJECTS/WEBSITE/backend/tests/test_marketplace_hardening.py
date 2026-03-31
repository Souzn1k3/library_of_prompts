from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.api.service_deps import build_marketplace_service
from app.infrastructure.db.models import (
    Category,
    CurrencyTransactionType,
    MarketplacePayout,
    MarketplacePayoutStatus,
    MarketplaceSettlementStatus,
    MarketplaceTransaction,
    ModerationState,
    PlanTier,
    PlanUsageWindow,
    Prompt,
    PromptPaymentMethod,
    PromptPrice,
    PromptPurchase,
    PromptEntitlement,
    PromptReview,
    PromptStatus,
    PromptTechnique,
    PurchaseStatus,
    ReviewModerationStatus,
)
from app.infrastructure.db.session import async_session_maker
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


async def _register_user(async_client, *, email: str, display_name: str) -> dict[str, str]:
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "display_name": display_name,
        },
    )
    assert response.status_code == 201, response.text
    token = response.json()["access_token"]
    me = await async_client.get("/api/v1/users/me", headers=_auth_headers(token))
    assert me.status_code == 200, me.text
    body = me.json()
    return {
        "token": token,
        "id": body["id"],
        "email": body["email"],
        "display_name": body["display_name"],
    }


async def _ensure_category(session) -> Category:
    existing = (await session.execute(select(Category).where(Category.slug == "pytest-marketplace"))).scalar_one_or_none()
    if existing is not None:
        return existing
    category = Category(
        slug="pytest-marketplace",
        name="Pytest Marketplace",
        sort_order=0,
        is_restricted=False,
    )
    session.add(category)
    await session.flush()
    return category


async def _create_prompt(
    *,
    author_id: str,
    slug: str,
    title: str,
    price_rub: int | None = None,
) -> tuple[str, str]:
    async with async_session_maker() as session:
        category = await _ensure_category(session)
        prompt = Prompt(
            slug=slug,
            title=title,
            body=f"{title} body.\n" * 24,
            summary=f"{title} summary",
            status=PromptStatus.published,
            technique=PromptTechnique.other,
            moderation_state=ModerationState.approved,
            category_id=category.id,
            author_id=UUID(author_id),
            is_premium=price_rub is not None,
        )
        session.add(prompt)
        await session.flush()
        if price_rub is not None:
            session.add(
                PromptPrice(
                    prompt_id=prompt.id,
                    price_rub=price_rub,
                    price_lumens=price_lumens_from_rub(price_rub),
                    commission_percent=5,
                    is_active=True,
                )
            )
            await session.flush()
        await session.commit()
        return str(prompt.id), prompt.slug


async def _credit_lumens(user_id: str, amount: int = 10_000) -> None:
    async with async_session_maker() as session:
        wallet = WalletRepository(session)
        await wallet.adjust_balance(
            user_id=UUID(user_id),
            amount=amount,
            reason=CurrencyTransactionType.manual_adjustment,
            context=f"tests:wallet:{user_id}:{amount}",
            metadata={"source": "pytest"},
        )
        await session.commit()


async def _set_free_plan_usage(user_id: str, *, used: int, total: int = 2) -> None:
    now = datetime.now(timezone.utc)
    started_at, ends_at = _billing_window(now)
    async with async_session_maker() as session:
        existing = (
            await session.execute(
                select(PlanUsageWindow).where(
                    PlanUsageWindow.user_id == UUID(user_id),
                    PlanUsageWindow.plan_tier == PlanTier.free,
                    PlanUsageWindow.window_started_at == started_at,
                    PlanUsageWindow.window_ends_at == ends_at,
                )
            )
        ).scalar_one_or_none()
        if existing is None:
            session.add(
                PlanUsageWindow(
                    user_id=UUID(user_id),
                    plan_tier=PlanTier.free,
                    window_started_at=started_at,
                    window_ends_at=ends_at,
                    included_paid_prompt_limit=total,
                    used_paid_prompt_unlocks=used,
                )
            )
        else:
            existing.included_paid_prompt_limit = total
            existing.used_paid_prompt_unlocks = used
        await session.commit()


async def _get_free_plan_usage_unlocks(user_id: str) -> int:
    now = datetime.now(timezone.utc)
    started_at, ends_at = _billing_window(now)
    async with async_session_maker() as session:
        row = (
            await session.execute(
                select(PlanUsageWindow).where(
                    PlanUsageWindow.user_id == UUID(user_id),
                    PlanUsageWindow.plan_tier == PlanTier.free,
                    PlanUsageWindow.window_started_at == started_at,
                    PlanUsageWindow.window_ends_at == ends_at,
                )
            )
        ).scalar_one_or_none()
        return int(row.used_paid_prompt_unlocks) if row is not None else 0


async def _purchase_with_lumens(async_client, *, token: str, prompt_id: str, client_token: str = "pytest-lumen-token"):
    response = await async_client.post(
        f"/api/v1/marketplace/prompts/{prompt_id}/buy-with-lumens",
        headers=_auth_headers(token),
        json={"client_token": client_token},
    )
    assert response.status_code == 200, response.text
    return response.json()


async def _purchase_with_checkout(async_client, *, token: str, prompt_id: str, client_token: str = "pytest-checkout-token"):
    response = await async_client.post(
        "/api/v1/marketplace/prompts/checkout-session",
        headers=_auth_headers(token),
        json={"prompt_id": prompt_id, "client_token": client_token},
    )
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.asyncio
async def test_paid_prompt_purchase_with_lumens_creates_entitlement_and_ledger(async_client, unique_email: str):
    seller = await _register_user(async_client, email=unique_email, display_name="Seller One")
    buyer = await _register_user(
        async_client,
        email=unique_email.replace("@", ".buyer@"),
        display_name="Buyer One",
    )
    prompt_id, slug = await _create_prompt(
        author_id=seller["id"],
        slug="pytest-paid-lumen-prompt",
        title="Pytest Paid Lumen Prompt",
        price_rub=250,
    )
    await _credit_lumens(buyer["id"], 5_000)

    payload = await _purchase_with_lumens(async_client, token=buyer["token"], prompt_id=prompt_id)
    purchase = payload["purchase"]
    assert purchase["payment_method"] == "lumens"
    assert purchase["status"] == "completed"
    assert purchase["settlement_status"] == "pending"
    assert payload["access"]["has_access"] is True

    detail = await async_client.get(f"/api/v1/prompts/by-slug/{slug}", headers=_auth_headers(buyer["token"]))
    assert detail.status_code == 200, detail.text
    detail_body = detail.json()
    assert detail_body["body_locked"] is False
    assert detail_body["access"]["has_access"] is True

    async with async_session_maker() as session:
        purchase_row = (
            await session.execute(select(PromptPurchase).where(PromptPurchase.id == UUID(purchase["id"])))
        ).scalar_one()
        assert purchase_row.completed_at is not None
        entitlement = (
            await session.execute(select(PromptEntitlement).where(PromptEntitlement.purchase_id == purchase_row.id))
        ).scalar_one()
        assert entitlement is not None
        assert entitlement.revoked_at is None
        ledger_rows = (
            await session.execute(
                select(MarketplaceTransaction.kind, MarketplaceTransaction.amount, MarketplaceTransaction.currency_code).where(
                    MarketplaceTransaction.prompt_purchase_id == purchase_row.id
                )
            )
        ).all()
        counts = Counter(kind.value for kind, _, _ in ledger_rows)
        assert counts["buyer_charge"] == 1
        assert counts["seller_credit"] == 1
        assert counts["platform_fee"] == 1
        assert purchase_row.platform_fee_lumens > 0
        assert purchase_row.seller_amount_lumens > 0


@pytest.mark.asyncio
async def test_own_prompt_blocking_and_quota_exhausted_buy_flow(async_client, unique_email: str):
    seller = await _register_user(async_client, email=unique_email, display_name="Seller Two")
    buyer = await _register_user(
        async_client,
        email=unique_email.replace("@", ".buyer2@"),
        display_name="Buyer Two",
    )
    prompt_id, slug = await _create_prompt(
        author_id=seller["id"],
        slug="pytest-paid-quota-prompt",
        title="Pytest Paid Quota Prompt",
        price_rub=190,
    )

    own_buy = await async_client.post(
        f"/api/v1/marketplace/prompts/{prompt_id}/buy-with-lumens",
        headers=_auth_headers(seller["token"]),
        json={"client_token": "seller-own-buy"},
    )
    assert own_buy.status_code == 400
    assert own_buy.json()["code"] == "cannot_buy_own_prompt"

    await _set_free_plan_usage(buyer["id"], used=2, total=2)
    catalog = await async_client.get("/api/v1/prompts", headers=_auth_headers(buyer["token"]))
    assert catalog.status_code == 200, catalog.text
    item = next(row for row in catalog.json() if row["id"] == prompt_id)
    assert item["access"]["catalog_action"] == "buy"
    assert item["access"]["purchase_required"] is True

    detail = await async_client.get(f"/api/v1/prompts/by-slug/{slug}", headers=_auth_headers(buyer["token"]))
    assert detail.status_code == 200, detail.text
    body = detail.json()
    assert body["body_locked"] is True
    assert body["access"]["catalog_action"] == "buy"
    assert body["access"]["purchase_required"] is True


@pytest.mark.asyncio
async def test_review_creation_update_and_refund_remove_review_from_rating(async_client, unique_email: str):
    seller = await _register_user(async_client, email=unique_email, display_name="Seller Reviews")
    buyer_one = await _register_user(
        async_client,
        email=unique_email.replace("@", ".buyer3@"),
        display_name="Buyer Reviews One",
    )
    buyer_two = await _register_user(
        async_client,
        email=unique_email.replace("@", ".buyer4@"),
        display_name="Buyer Reviews Two",
    )
    prompt_one_id, _ = await _create_prompt(
        author_id=seller["id"],
        slug="pytest-review-prompt-one",
        title="Pytest Review Prompt One",
        price_rub=220,
    )
    prompt_two_id, _ = await _create_prompt(
        author_id=seller["id"],
        slug="pytest-review-prompt-two",
        title="Pytest Review Prompt Two",
        price_rub=220,
    )
    await _credit_lumens(buyer_one["id"], 5_000)
    await _credit_lumens(buyer_two["id"], 5_000)

    purchase_one = await _purchase_with_lumens(
        async_client,
        token=buyer_one["token"],
        prompt_id=prompt_one_id,
        client_token="review-one",
    )
    purchase_two = await _purchase_with_lumens(
        async_client,
        token=buyer_two["token"],
        prompt_id=prompt_two_id,
        client_token="review-two",
    )

    create_review = await async_client.put(
        f"/api/v1/marketplace/prompts/{prompt_one_id}/review",
        headers=_auth_headers(buyer_one["token"]),
        json={"rating": 5, "text": "Excellent structure and clear output framing."},
    )
    assert create_review.status_code == 200, create_review.text
    review_id = create_review.json()["id"]
    assert create_review.json()["moderation_status"] == "visible"

    async with async_session_maker() as session:
        await session.execute(
            update(PromptReview)
            .where(PromptReview.id == UUID(review_id))
            .values(updated_at=datetime.now(timezone.utc) - timedelta(minutes=20))
        )
        await session.commit()

    update_review = await async_client.put(
        f"/api/v1/marketplace/prompts/{prompt_one_id}/review",
        headers=_auth_headers(buyer_one["token"]),
        json={"rating": 4, "text": "Still good after a second pass, but needs a stronger example."},
    )
    assert update_review.status_code == 200, update_review.text
    assert update_review.json()["id"] == review_id
    assert update_review.json()["rating"] == 4

    second_review = await async_client.put(
        f"/api/v1/marketplace/prompts/{prompt_two_id}/review",
        headers=_auth_headers(buyer_two["token"]),
        json={"rating": 2, "text": "Too generic for the price."},
    )
    assert second_review.status_code == 200, second_review.text

    async with async_session_maker() as session:
        svc = build_marketplace_service(session)
        refunded = await svc.refund_purchase_by_id(purchase_id=UUID(purchase_two["purchase"]["id"]), reason="buyer_requested")
        assert refunded is not None
        await session.commit()

    blocked = await async_client.put(
        f"/api/v1/marketplace/prompts/{prompt_two_id}/review",
        headers=_auth_headers(buyer_two["token"]),
        json={"rating": 3, "text": "Trying again after refund."},
    )
    assert blocked.status_code == 403

    async with async_session_maker() as session:
        review_rows = (
            await session.execute(
                select(PromptReview).where(PromptReview.prompt_purchase_id == UUID(purchase_one["purchase"]["id"]))
            )
        ).scalars().all()
        assert len(review_rows) == 1
        assert review_rows[0].edit_count == 1

        refunded_review = (
            await session.execute(
                select(PromptReview).where(PromptReview.prompt_purchase_id == UUID(purchase_two["purchase"]["id"]))
            )
        ).scalar_one()
        assert refunded_review.moderation_status == ReviewModerationStatus.hidden
        assert refunded_review.is_visible is False

        svc = build_marketplace_service(session)
        summary = await svc.seller_summary(seller_user_id=UUID(seller["id"]))
        assert summary.review_count == 1
        assert summary.rating_display == 4.0


@pytest.mark.asyncio
async def test_review_reporting_hides_review_after_threshold(async_client, unique_email: str):
    seller = await _register_user(async_client, email=unique_email, display_name="Seller Reports")
    buyer = await _register_user(
        async_client,
        email=unique_email.replace("@", ".buyer5@"),
        display_name="Buyer Reports",
    )
    reporters = [
        await _register_user(async_client, email=unique_email.replace("@", f".report{i}@"), display_name=f"Reporter {i}")
        for i in range(1, 4)
    ]
    prompt_id, _ = await _create_prompt(
        author_id=seller["id"],
        slug="pytest-report-prompt",
        title="Pytest Report Prompt",
        price_rub=260,
    )
    await _credit_lumens(buyer["id"], 5_000)

    purchase = await _purchase_with_lumens(async_client, token=buyer["token"], prompt_id=prompt_id, client_token="report-purchase")
    review = await async_client.put(
        f"/api/v1/marketplace/prompts/{prompt_id}/review",
        headers=_auth_headers(buyer["token"]),
        json={"rating": 1, "text": "Spammy behavior for abuse-report testing."},
    )
    assert review.status_code == 200, review.text
    review_id = review.json()["id"]

    for index, reporter in enumerate(reporters, start=1):
        report = await async_client.post(
            f"/api/v1/marketplace/reviews/{review_id}/report",
            headers=_auth_headers(reporter["token"]),
            json={"reason": "spam", "details": f"report-{index}"},
        )
        assert report.status_code == 200, report.text

    async with async_session_maker() as session:
        flagged_review = (await session.execute(select(PromptReview).where(PromptReview.id == UUID(review_id)))).scalar_one()
        assert flagged_review.reported_count == 3
        assert flagged_review.moderation_status == ReviewModerationStatus.hidden
        assert flagged_review.is_visible is False

        svc = build_marketplace_service(session)
        summary = await svc.seller_summary(seller_user_id=UUID(seller["id"]))
        assert summary.review_count == 0


@pytest.mark.asyncio
async def test_suspicious_repeat_buyer_seller_pattern_goes_pending(async_client, unique_email: str):
    seller = await _register_user(async_client, email=unique_email, display_name="Seller Suspicious")
    buyer = await _register_user(
        async_client,
        email=unique_email.replace("@", ".buyer6@"),
        display_name="Buyer Suspicious",
    )
    await _credit_lumens(buyer["id"], 10_000)
    prompt_ids: list[str] = []
    for index in range(3):
        prompt_id, _ = await _create_prompt(
            author_id=seller["id"],
            slug=f"pytest-suspicious-prompt-{index}",
            title=f"Pytest Suspicious Prompt {index}",
            price_rub=180,
        )
        prompt_ids.append(prompt_id)
        await _purchase_with_lumens(
            async_client,
            token=buyer["token"],
            prompt_id=prompt_id,
            client_token=f"suspicious-{index}",
        )

    review = await async_client.put(
        f"/api/v1/marketplace/prompts/{prompt_ids[-1]}/review",
        headers=_auth_headers(buyer["token"]),
        json={"rating": 5, "text": "This should be held because the buyer-seller pattern is suspicious."},
    )
    assert review.status_code == 200, review.text
    assert review.json()["moderation_status"] == "pending"
    assert review.json()["moderation_reason"] == "dense_buyer_seller_activity"


@pytest.mark.asyncio
async def test_settlement_and_payout_lifecycle_keeps_ledger_consistent(async_client, unique_email: str):
    seller = await _register_user(async_client, email=unique_email, display_name="Seller Payouts")
    buyer = await _register_user(
        async_client,
        email=unique_email.replace("@", ".buyer7@"),
        display_name="Buyer Payouts",
    )
    prompt_one_id, _ = await _create_prompt(
        author_id=seller["id"],
        slug="pytest-payout-prompt-one",
        title="Pytest Payout Prompt One",
        price_rub=300,
    )
    prompt_two_id, _ = await _create_prompt(
        author_id=seller["id"],
        slug="pytest-payout-prompt-two",
        title="Pytest Payout Prompt Two",
        price_rub=320,
    )

    checkout_one = await _purchase_with_checkout(
        async_client,
        token=buyer["token"],
        prompt_id=prompt_one_id,
        client_token="checkout-one",
    )
    checkout_two = await _purchase_with_checkout(
        async_client,
        token=buyer["token"],
        prompt_id=prompt_two_id,
        client_token="checkout-two",
    )

    async with async_session_maker() as session:
        svc = build_marketplace_service(session)

        purchase_one = (await session.execute(select(PromptPurchase).where(PromptPurchase.id == UUID(checkout_one["purchase_id"])))).scalar_one()
        purchase_two = (await session.execute(select(PromptPurchase).where(PromptPurchase.id == UUID(checkout_two["purchase_id"])))).scalar_one()
        release_at = max(purchase_one.settlement_available_at, purchase_two.settlement_available_at) + timedelta(minutes=1)
        released = await svc.refresh_settlement_states(seller_user_id=UUID(seller["id"]), now=release_at)
        assert released == 2

        first_payout = await svc.create_payout_batch(seller_user_id=UUID(seller["id"]), currency_code="RUB", notes="first batch")
        assert first_payout.status == MarketplacePayoutStatus.requested
        first_payout_row = (await session.execute(select(MarketplacePayout).where(MarketplacePayout.id == first_payout.id))).scalar_one()
        assert first_payout_row.purchase_count == 2

        refunded = await svc.refund_purchase_by_id(purchase_id=purchase_one.id, reason="pre_payout_refund")
        assert refunded is not None
        refreshed_first_payout = await svc.mark_payout_processing(payout_id=first_payout.id)
        assert refreshed_first_payout.purchase_count == 1
        assert refreshed_first_payout.status == MarketplacePayoutStatus.processing
        finalized_first = await svc.finalize_payout(payout_id=first_payout.id, reference="batch-001")
        assert finalized_first.status == MarketplacePayoutStatus.paid
        assert finalized_first.purchase_count == 1

        await session.commit()

    async with async_session_maker() as session:
        purchase_one = (await session.execute(select(PromptPurchase).where(PromptPurchase.id == UUID(checkout_one["purchase_id"])))).scalar_one()
        purchase_two = (await session.execute(select(PromptPurchase).where(PromptPurchase.id == UUID(checkout_two["purchase_id"])))).scalar_one()
        assert purchase_one.status == PurchaseStatus.refunded
        assert purchase_one.settlement_status == MarketplaceSettlementStatus.refunded
        assert purchase_two.status == PurchaseStatus.completed
        assert purchase_two.settlement_status == MarketplaceSettlementStatus.paid_out

        ledger_rows = (
            await session.execute(
                select(MarketplaceTransaction.kind, MarketplaceTransaction.amount).where(
                    MarketplaceTransaction.prompt_purchase_id.in_([purchase_one.id, purchase_two.id])
                )
            )
        ).all()
        counts = Counter(kind.value for kind, _ in ledger_rows)
        assert counts["buyer_charge"] == 2
        assert counts["platform_fee"] == 2
        assert counts["seller_credit"] == 2
        assert counts["seller_available"] == 2
        assert counts["refund"] == 1
        assert counts["seller_reversal"] == 1
        assert counts["seller_payout"] == 1

        svc = build_marketplace_service(session)
        summary = await svc.seller_summary(seller_user_id=UUID(seller["id"]))
        assert summary.available_balance_rub == 0
        assert summary.paid_out_rub == purchase_two.seller_amount_rub
        assert summary.refunded_balance_rub == purchase_one.seller_amount_rub
        assert summary.clawback_due_rub == 0


@pytest.mark.asyncio
async def test_pending_purchase_unique_index_prevents_duplicate_pending_rows(async_client, unique_email: str):
    seller = await _register_user(async_client, email=unique_email, display_name="Seller Race")
    buyer = await _register_user(
        async_client,
        email=unique_email.replace("@", ".buyer8@"),
        display_name="Buyer Race",
    )
    prompt_id, _ = await _create_prompt(
        author_id=seller["id"],
        slug="pytest-pending-unique-prompt",
        title="Pytest Pending Unique Prompt",
        price_rub=205,
    )

    async with async_session_maker() as session:
        first = PromptPurchase(
            user_id=UUID(buyer["id"]),
            prompt_id=UUID(prompt_id),
            seller_user_id=UUID(seller["id"]),
            payment_method=PromptPaymentMethod.stripe,
            status=PurchaseStatus.pending,
            price_rub=205,
            seller_amount_rub=194,
            platform_fee_rub=11,
            client_token="pending-1",
        )
        session.add(first)
        await session.flush()

        session.add(
            PromptPurchase(
                user_id=UUID(buyer["id"]),
                prompt_id=UUID(prompt_id),
                seller_user_id=UUID(seller["id"]),
                payment_method=PromptPaymentMethod.stripe,
                status=PurchaseStatus.pending,
                price_rub=205,
                seller_amount_rub=194,
                platform_fee_rub=11,
                client_token="pending-2",
            )
        )
        with pytest.raises(IntegrityError):
            await session.flush()
        await session.rollback()


@pytest.mark.asyncio
async def test_cross_site_prompt_get_does_not_consume_included_unlock(async_client, unique_email: str):
    seller = await _register_user(async_client, email=unique_email, display_name="Seller Cross Site")
    buyer = await _register_user(
        async_client,
        email=unique_email.replace("@", ".buyer-cross@"),
        display_name="Buyer Cross Site",
    )
    prompt_id, slug = await _create_prompt(
        author_id=seller["id"],
        slug="pytest-cross-site-unlock-prompt",
        title="Pytest Cross Site Unlock Prompt",
        price_rub=210,
    )
    assert prompt_id

    await _set_free_plan_usage(buyer["id"], used=0, total=2)

    cross_site = await async_client.get(
        f"/api/v1/prompts/by-slug/{slug}",
        headers={**_auth_headers(buyer["token"]), "Sec-Fetch-Site": "cross-site"},
    )
    assert cross_site.status_code == 200, cross_site.text
    cross_body = cross_site.json()
    assert cross_body["body_locked"] is True
    assert cross_body["access"]["has_access"] is False
    assert cross_body["access"]["can_unlock_with_plan"] is True
    assert cross_body["access"]["remaining_plan_unlocks"] == 2
    assert await _get_free_plan_usage_unlocks(buyer["id"]) == 0

    same_site = await async_client.get(
        f"/api/v1/prompts/by-slug/{slug}",
        headers=_auth_headers(buyer["token"]),
    )
    assert same_site.status_code == 200, same_site.text
    same_body = same_site.json()
    assert same_body["body_locked"] is False
    assert same_body["access"]["has_access"] is True
    assert same_body["access"]["source"] == "subscription_limit"
    assert await _get_free_plan_usage_unlocks(buyer["id"]) == 1


@pytest.mark.asyncio
async def test_checkout_session_rejects_untrusted_redirect_urls(async_client, unique_email: str):
    seller = await _register_user(async_client, email=unique_email, display_name="Seller Redirect")
    buyer = await _register_user(
        async_client,
        email=unique_email.replace("@", ".buyer-redirect@"),
        display_name="Buyer Redirect",
    )
    prompt_id, _ = await _create_prompt(
        author_id=seller["id"],
        slug="pytest-redirect-guard-prompt",
        title="Pytest Redirect Guard Prompt",
        price_rub=260,
    )

    response = await async_client.post(
        "/api/v1/marketplace/prompts/checkout-session",
        headers=_auth_headers(buyer["token"]),
        json={
            "prompt_id": prompt_id,
            "client_token": "redirect-guard-001",
            "success_url": "https://evil.example/checkout/hijack",
        },
    )
    assert response.status_code == 400, response.text
    body = response.json()
    assert body["code"] == "invalid_redirect_url"


@pytest.mark.asyncio
async def test_marketplace_rejects_invalid_payout_currency(async_client, unique_email: str):
    seller = await _register_user(async_client, email=unique_email, display_name="Seller Invalid Currency")

    response = await async_client.post(
        "/api/v1/marketplace/payouts/request",
        headers=_auth_headers(seller["token"]),
        json={"currency_code": "USD"},
    )
    assert response.status_code == 422, response.text
    body = response.json()
    assert body["code"] == "validation_error"
    assert any("currency_code must be RUB or LMN" in err.get("msg", "") for err in body["details"]["errors"])


@pytest.mark.asyncio
async def test_lumen_purchase_client_token_is_scoped_per_user(async_client, unique_email: str):
    seller = await _register_user(async_client, email=unique_email, display_name="Seller Token Scope")
    buyer_one = await _register_user(
        async_client,
        email=unique_email.replace("@", ".buyer-scope-1@"),
        display_name="Buyer Scope One",
    )
    buyer_two = await _register_user(
        async_client,
        email=unique_email.replace("@", ".buyer-scope-2@"),
        display_name="Buyer Scope Two",
    )
    await _credit_lumens(buyer_one["id"], 8_000)
    await _credit_lumens(buyer_two["id"], 8_000)
    prompt_id, _ = await _create_prompt(
        author_id=seller["id"],
        slug="pytest-lumen-token-scope-prompt",
        title="Pytest Lumen Token Scope Prompt",
        price_rub=230,
    )

    first = await _purchase_with_lumens(
        async_client,
        token=buyer_one["token"],
        prompt_id=prompt_id,
        client_token="shared-marketplace-token",
    )
    second = await _purchase_with_lumens(
        async_client,
        token=buyer_two["token"],
        prompt_id=prompt_id,
        client_token="shared-marketplace-token",
    )
    assert first["purchase"]["id"] != second["purchase"]["id"]
