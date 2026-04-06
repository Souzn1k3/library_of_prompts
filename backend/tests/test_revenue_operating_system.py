from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import update, select

from app.infrastructure.db.models import SessionAttribution, User, UserAttribution, UserRole
from app.infrastructure.db.session import async_session_maker


async def _promote_to_admin(email: str) -> None:
    async with async_session_maker() as session:
        await session.execute(update(User).where(User.email == email.lower()).values(role=UserRole.admin))
        await session.commit()


@pytest.mark.asyncio
async def test_attribution_capture_persists_first_and_last_touch(async_client, unique_email: str):
    session_id = f"session-{unique_email[:8]}"
    guest_capture = await async_client.post(
        "/api/v1/analytics/attribution",
        json={
            "session_id": session_id,
            "source": "web",
            "attribution": {
                "utm_source": "google",
                "utm_medium": "cpc",
                "utm_campaign": "launch",
                "referrer": "https://example.com",
            },
        },
    )
    assert guest_capture.status_code == 200

    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "password123",
            "display_name": "Attr User",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]

    user_capture = await async_client.post(
        "/api/v1/analytics/attribution",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "session_id": session_id,
            "source": "web",
            "attribution": {
                "utm_source": "newsletter",
                "utm_medium": "email",
                "utm_campaign": "drip_1",
                "referrer": "https://mail.example.com",
            },
        },
    )
    assert user_capture.status_code == 200
    payload = user_capture.json()
    assert payload["first_touch"]["utm_source"] == "google"
    assert payload["last_touch"]["utm_source"] == "newsletter"

    async with async_session_maker() as session:
        user_row = await session.scalar(select(User).where(User.email == unique_email.lower()))
        assert user_row is not None
        session_attr = await session.scalar(
            select(SessionAttribution).where(SessionAttribution.session_id == session_id)
        )
        user_attr = await session.scalar(select(UserAttribution).where(UserAttribution.user_id == user_row.id))
        assert session_attr is not None
        assert user_attr is not None
        assert session_attr.first_utm_source == "google"
        assert session_attr.last_utm_source == "newsletter"
        assert user_attr.first_utm_source == "google"
        assert user_attr.last_utm_source == "newsletter"


@pytest.mark.asyncio
async def test_revenue_events_emitted_on_checkout(async_client, unique_email: str):
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "password123",
            "display_name": "Revenue User",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    await _promote_to_admin(unique_email)

    capture = await async_client.post(
        "/api/v1/analytics/attribution",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "session_id": "checkout-session-1",
            "source": "web",
            "attribution": {
                "utm_source": "twitter",
                "utm_medium": "social",
                "utm_campaign": "creator_launch",
            },
        },
    )
    assert capture.status_code == 200

    checkout = await async_client.post(
        "/api/v1/billing/checkout/session",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "tier": "starter",
            "source_page": "/pricing",
            "scenario_slug": "revenue-test-scenario",
            "paywall_variant": "value_focused",
            "pricing_variant": "operator_pack",
        },
    )
    assert checkout.status_code == 200

    login_admin = await async_client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": "password123"},
    )
    assert login_admin.status_code == 200
    admin_token = login_admin.json()["access_token"]
    recent = await async_client.get(
        "/api/v1/analytics/events/recent?limit=200&hours=24",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert recent.status_code == 200
    names = {event["event_name"] for event in recent.json()}
    assert "checkout_started" in names
    assert "checkout_completed" in names
    assert "subscription_started" in names


@pytest.mark.asyncio
async def test_revenue_dashboard_returns_metrics(async_client, unique_email: str):
    admin_email = unique_email
    payer_email = f"payer_{unique_email}"

    reg_admin = await async_client.post(
        "/api/v1/auth/register",
        json={"email": admin_email, "password": "password123", "display_name": "Revenue Admin"},
    )
    assert reg_admin.status_code == 201
    await _promote_to_admin(admin_email)
    login_admin = await async_client.post(
        "/api/v1/auth/login",
        json={"email": admin_email, "password": "password123"},
    )
    assert login_admin.status_code == 200
    admin_token = login_admin.json()["access_token"]

    reg_payer = await async_client.post(
        "/api/v1/auth/register",
        json={"email": payer_email, "password": "password123", "display_name": "Revenue Payer"},
    )
    assert reg_payer.status_code == 201
    payer_token = reg_payer.json()["access_token"]

    capture = await async_client.post(
        "/api/v1/analytics/attribution",
        headers={"Authorization": f"Bearer {payer_token}"},
        json={
            "session_id": "revenue-dashboard-session",
            "source": "web",
            "attribution": {
                "utm_source": "linkedin",
                "utm_medium": "paid_social",
                "utm_campaign": "b2b",
            },
        },
    )
    assert capture.status_code == 200

    ingest = await async_client.post(
        "/api/v1/analytics/events",
        headers={"Authorization": f"Bearer {payer_token}"},
        json={
            "events": [
                {
                    "event_id": f"paywall_view_{unique_email[:8]}",
                    "event_name": "paywall_viewed",
                    "session_id": "revenue-dashboard-session",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "context": {"page": "/pricing", "feature": "pytest_revenue"},
                    "metadata": {"paywall_variant": "value_focused", "pricing_variant": "operator_pack"},
                    "source": "pytest",
                },
                {
                    "event_id": f"paywall_interaction_{unique_email[:8]}",
                    "event_name": "paywall_interaction",
                    "session_id": "revenue-dashboard-session",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "context": {"page": "/pricing", "feature": "pytest_revenue"},
                    "metadata": {"paywall_variant": "value_focused", "pricing_variant": "operator_pack"},
                    "source": "pytest",
                },
            ]
        },
    )
    assert ingest.status_code == 202

    checkout = await async_client.post(
        "/api/v1/billing/checkout/session",
        headers={"Authorization": f"Bearer {payer_token}"},
        json={
            "tier": "starter",
            "source_page": "/pricing",
            "paywall_variant": "value_focused",
            "pricing_variant": "operator_pack",
        },
    )
    assert checkout.status_code == 200

    dashboard = await async_client.get(
        "/api/v1/analytics/revenue/dashboard?window_days=30",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert dashboard.status_code == 200
    payload = dashboard.json()
    assert payload["headline"]["mrr_usd"] >= 0
    assert payload["headline"]["arr_usd"] >= payload["headline"]["mrr_usd"]
    assert payload["funnel"]["steps"]
    assert payload["revenue_by_source"]
    assert payload["paywall_performance"]
    assert "churn_signals" in payload

