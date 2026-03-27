"""Stripe webhook: real HMAC signatures, idempotency, and subscription sync (no live Stripe API for subscription.updated)."""

from __future__ import annotations

import json
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.infrastructure.db.models import BillingCustomer, BillingProvider
from app.infrastructure.db.session import async_session_maker

from tests.helpers.stripe_webhook import (
    event_json_bytes,
    sign_stripe_webhook_payload,
    subscription_updated_event,
)

WEBHOOK_SECRET = "whsec_test_signing_secret_must_be_32_chars_min!!"


@pytest.fixture
def stripe_webhook_env(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import get_settings

    monkeypatch.setenv("BILLING_MOCK_MODE", "false")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_12345678901234567890123456789012")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WEBHOOK_SECRET)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest_asyncio.fixture
async def async_client(stripe_webhook_env: None) -> AsyncClient:
    from app.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def _attach_stripe_customer(*, user_id: uuid.UUID, email: str, customer_id: str) -> None:
    async with async_session_maker() as session:
        session.add(
            BillingCustomer(
                user_id=user_id,
                provider=BillingProvider.stripe,
                provider_customer_id=customer_id,
                email=email,
            )
        )
        await session.commit()


@pytest.mark.asyncio
async def test_webhook_signature_round_trip_matches_stripe_sdk(async_client: AsyncClient) -> None:
    import stripe

    payload_dict = {"id": "evt_sig_test", "type": "ping", "data": {"object": {}}}
    raw = json.dumps(payload_dict, separators=(",", ":")).encode("utf-8")
    header = sign_stripe_webhook_payload(payload_bytes=raw, secret=WEBHOOK_SECRET)
    event = stripe.Webhook.construct_event(raw, header, WEBHOOK_SECRET)
    assert event["id"] == "evt_sig_test"


@pytest.mark.asyncio
async def test_signed_subscription_webhook_updates_user_tier(
    async_client: AsyncClient,
    unique_email: str,
) -> None:
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "password123",
            "display_name": "Stripe User",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    me = await async_client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    user_id = uuid.UUID(me.json()["id"])
    customer_id = f"cus_test_{uuid.uuid4().hex[:12]}"
    await _attach_stripe_customer(user_id=user_id, email=unique_email, customer_id=customer_id)

    event_id = f"evt_{uuid.uuid4().hex}"
    sub_id = f"sub_{uuid.uuid4().hex[:16]}"
    ev = subscription_updated_event(
        event_id=event_id,
        customer_id=customer_id,
        subscription_id=sub_id,
        tier="starter",
    )
    raw = json.dumps(ev, separators=(",", ":")).encode("utf-8")
    sig = sign_stripe_webhook_payload(payload_bytes=raw, secret=WEBHOOK_SECRET)

    wh = await async_client.post(
        "/api/v1/billing/webhooks",
        content=raw,
        headers={"Stripe-Signature": sig},
    )
    assert wh.status_code == 200
    assert wh.json().get("status") == "ok"

    me2 = await async_client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me2.json()["plan_tier"] == "starter"


@pytest.mark.asyncio
async def test_webhook_idempotent_duplicate_event_id(
    async_client: AsyncClient,
    unique_email: str,
) -> None:
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "password123",
            "display_name": "Dup User",
        },
    )
    token = reg.json()["access_token"]
    me = await async_client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    user_id = uuid.UUID(me.json()["id"])
    customer_id = f"cus_dup_{uuid.uuid4().hex[:12]}"
    await _attach_stripe_customer(user_id=user_id, email=unique_email, customer_id=customer_id)

    event_id = f"evt_dup_{uuid.uuid4().hex}"
    ev = subscription_updated_event(
        event_id=event_id,
        customer_id=customer_id,
        subscription_id=f"sub_{uuid.uuid4().hex[:12]}",
        tier="pro",
    )
    raw = json.dumps(ev, separators=(",", ":")).encode("utf-8")
    sig = sign_stripe_webhook_payload(payload_bytes=raw, secret=WEBHOOK_SECRET)

    first = await async_client.post(
        "/api/v1/billing/webhooks",
        content=raw,
        headers={"Stripe-Signature": sig},
    )
    assert first.status_code == 200
    assert first.json().get("status") == "ok"

    second = await async_client.post(
        "/api/v1/billing/webhooks",
        content=raw,
        headers={"Stripe-Signature": sig},
    )
    assert second.status_code == 200
    assert second.json().get("status") == "duplicate"


@pytest.mark.asyncio
async def test_webhook_rejects_bad_signature(async_client: AsyncClient) -> None:
    ev = subscription_updated_event(
        event_id="evt_bad_sig",
        customer_id="cus_x",
        subscription_id="sub_x",
        tier="starter",
    )
    raw = json.dumps(ev, separators=(",", ":")).encode("utf-8")
    bad_sig = sign_stripe_webhook_payload(
        payload_bytes=raw,
        secret="whsec_wrong_secret_also_needs_32_chars_min!!",
    )
    r = await async_client.post(
        "/api/v1/billing/webhooks",
        content=raw,
        headers={"Stripe-Signature": bad_sig},
    )
    assert r.status_code == 400
    assert r.json().get("code") == "invalid_webhook_signature"
