from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import select, update

from app.infrastructure.db.models import User, UserRole
from app.infrastructure.db.session import async_session_maker


async def _promote_to_admin(email: str) -> None:
    async with async_session_maker() as session:
        await session.execute(update(User).where(User.email == email.lower()).values(role=UserRole.admin))
        await session.commit()


@pytest.mark.asyncio
async def test_channel_attribution_tracks_ad_click_and_landing_view(async_client, unique_email: str):
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "password123",
            "display_name": "GTM User",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    await _promote_to_admin(unique_email)

    capture = await async_client.post(
        "/api/v1/analytics/attribution",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "session_id": "gtm-attr-session-1",
            "source": "web",
            "page": "/",
            "feature": "pytest",
            "attribution": {
                "utm_source": "google",
                "utm_medium": "ads",
                "utm_campaign": "search_launch",
                "ad_id": "ad_44",
                "creative_id": "creative_2",
                "referrer": "https://google.com",
            },
        },
    )
    assert capture.status_code == 200
    payload = capture.json()
    assert payload["first_touch"]["ad_id"] == "ad_44"
    assert payload["last_touch"]["creative_id"] == "creative_2"

    recent = await async_client.get(
        "/api/v1/analytics/events/recent?limit=200&hours=24",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert recent.status_code == 200
    event_names = {row["event_name"] for row in recent.json()}
    assert "ad_click" in event_names
    assert "landing_view" in event_names
    assert "attribution_assigned" in event_names


@pytest.mark.asyncio
async def test_gtm_spend_upsert_is_idempotent(async_client, unique_email: str):
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "password123",
            "display_name": "GTM Spend Admin",
        },
    )
    assert reg.status_code == 201
    await _promote_to_admin(unique_email)
    login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": "password123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    first = await async_client.post(
        "/api/v1/analytics/gtm/spend",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "spend_day": "2026-04-01",
            "source": "google",
            "medium": "ads",
            "campaign": "search_launch",
            "ad_id": "ad_44",
            "creative_id": "creative_2",
            "cost_usd": 100.0,
            "clicks": 500,
            "impressions": 9000,
            "dedupe_key": "google-search-launch-20260401",
        },
    )
    assert first.status_code == 200
    assert first.json()["cost_usd"] == 100.0

    second = await async_client.post(
        "/api/v1/analytics/gtm/spend",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "spend_day": "2026-04-01",
            "source": "google",
            "medium": "ads",
            "campaign": "search_launch",
            "ad_id": "ad_44",
            "creative_id": "creative_2",
            "cost_usd": 135.0,
            "clicks": 610,
            "impressions": 11000,
            "dedupe_key": "google-search-launch-20260401",
        },
    )
    assert second.status_code == 200
    assert second.json()["cost_usd"] == 135.0
    assert second.json()["clicks"] == 610
    assert second.json()["id"] == first.json()["id"]


@pytest.mark.asyncio
async def test_gtm_dashboard_exposes_cac_roi_and_signals(async_client, unique_email: str):
    admin_email = unique_email
    payer_email = f"payer_{unique_email}"

    reg_admin = await async_client.post(
        "/api/v1/auth/register",
        json={"email": admin_email, "password": "password123", "display_name": "GTM Admin"},
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
        json={"email": payer_email, "password": "password123", "display_name": "GTM Payer"},
    )
    assert reg_payer.status_code == 201
    payer_token = reg_payer.json()["access_token"]

    capture = await async_client.post(
        "/api/v1/analytics/attribution",
        headers={"Authorization": f"Bearer {payer_token}"},
        json={
            "session_id": "gtm-dashboard-session",
            "source": "web",
            "page": "/",
            "feature": "pytest_gtm",
            "attribution": {
                "utm_source": "google",
                "utm_medium": "ads",
                "utm_campaign": "search_launch",
                "ad_id": "ad_44",
                "creative_id": "creative_2",
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
                    "event_id": f"gtm_scenario_run_{unique_email[:8]}",
                    "event_name": "scenario_run",
                    "session_id": "gtm-dashboard-session",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "context": {"page": "/", "feature": "pytest_gtm"},
                    "metadata": {"prompt_slug": "pytest-scenario"},
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
            "scenario_slug": "pytest-scenario",
            "paywall_variant": "value_focused",
            "pricing_variant": "operator_pack",
        },
    )
    assert checkout.status_code == 200

    spend = await async_client.post(
        "/api/v1/analytics/gtm/spend",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "spend_day": datetime.now(timezone.utc).date().isoformat(),
            "source": "google",
            "medium": "ads",
            "campaign": "search_launch",
            "ad_id": "ad_44",
            "creative_id": "creative_2",
            "cost_usd": 150.0,
            "clicks": 800,
            "impressions": 12000,
        },
    )
    assert spend.status_code == 200

    dashboard = await async_client.get(
        "/api/v1/analytics/gtm/dashboard?window_days=30",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert dashboard.status_code == 200
    payload = dashboard.json()
    assert payload["headline"]["revenue_usd"] >= 0
    assert payload["headline"]["spend_usd"] >= 150.0
    assert payload["channels"]
    assert payload["funnel_by_source"]
    assert payload["top_campaigns"]
    assert payload["top_creatives"]
    assert any(signal["signal"] == "kill_channel" for signal in payload["signals"])

    async with async_session_maker() as session:
        user_row = await session.scalar(select(User).where(User.email == payer_email.lower()))
        assert user_row is not None

    recent = await async_client.get(
        "/api/v1/analytics/events/recent?limit=300&hours=24",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert recent.status_code == 200
    names = {event["event_name"] for event in recent.json()}
    assert "scale_channel" in names or "kill_channel" in names

