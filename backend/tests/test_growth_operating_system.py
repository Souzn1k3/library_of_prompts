from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import update

from app.infrastructure.db.models import User, UserRole
from app.infrastructure.db.session import async_session_maker


async def _promote_to_admin(email: str) -> None:
    async with async_session_maker() as session:
        await session.execute(
            update(User).where(User.email == email.lower()).values(role=UserRole.admin),
        )
        await session.commit()


@pytest.mark.asyncio
async def test_growth_runtime_returns_deterministic_assignments(async_client):
    r1 = await async_client.get(
        "/api/v1/analytics/growth/runtime",
        params={
            "session_id": "guest-session-growth",
            "page": "/",
            "feature": "pytest_growth",
        },
    )
    assert r1.status_code == 200
    body1 = r1.json()
    assert body1["flags"]
    assert body1["experiments"]

    r2 = await async_client.get(
        "/api/v1/analytics/growth/runtime",
        params={
            "session_id": "guest-session-growth",
            "page": "/",
            "feature": "pytest_growth",
        },
    )
    assert r2.status_code == 200
    body2 = r2.json()

    assert body1["flags"] == body2["flags"]
    assert body1["experiments"] == body2["experiments"]


@pytest.mark.asyncio
async def test_growth_dashboard_requires_admin(async_client, unique_email: str):
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "password123",
            "display_name": "Growth User",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]

    forbidden = await async_client.get(
        "/api/v1/analytics/growth/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert forbidden.status_code == 403


@pytest.mark.asyncio
async def test_growth_dashboard_aggregates_metrics(async_client, unique_email: str):
    admin_email = unique_email
    user_email = f"metrics_{unique_email}"

    reg_admin = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": admin_email,
            "password": "password123",
            "display_name": "Growth Admin",
        },
    )
    assert reg_admin.status_code == 201
    await _promote_to_admin(admin_email)

    login_admin = await async_client.post(
        "/api/v1/auth/login",
        json={"email": admin_email, "password": "password123"},
    )
    assert login_admin.status_code == 200
    admin_token = login_admin.json()["access_token"]

    reg_user = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": user_email,
            "password": "password123",
            "display_name": "Growth Metrics User",
        },
    )
    assert reg_user.status_code == 201
    user_token = reg_user.json()["access_token"]

    now = datetime.now(timezone.utc)
    event_base = unique_email.replace("@", "_")
    events = [
        {
            "event_id": f"{event_base}_signup",
            "event_name": "signup_completed",
            "session_id": "growth_metrics_session",
            "timestamp": (now - timedelta(days=8)).isoformat(),
            "context": {"page": "/signup", "feature": "pytest_growth"},
            "metadata": {},
            "source": "pytest",
        },
        {
            "event_id": f"{event_base}_run",
            "event_name": "scenario_run",
            "session_id": "growth_metrics_session",
            "timestamp": (now - timedelta(days=8, hours=-1)).isoformat(),
            "context": {"page": "/", "feature": "pytest_growth"},
            "metadata": {},
            "source": "pytest",
        },
        {
            "event_id": f"{event_base}_save",
            "event_name": "scenario_saved",
            "session_id": "growth_metrics_session",
            "timestamp": (now - timedelta(days=7, hours=18)).isoformat(),
            "context": {"page": "/", "feature": "pytest_growth"},
            "metadata": {},
            "source": "pytest",
        },
        {
            "event_id": f"{event_base}_resume",
            "event_name": "scenario_resumed",
            "session_id": "growth_metrics_session",
            "timestamp": (now - timedelta(days=7)).isoformat(),
            "context": {"page": "/", "feature": "pytest_growth"},
            "metadata": {},
            "source": "pytest",
        },
        {
            "event_id": f"{event_base}_upgrade_click",
            "event_name": "scenario_upgrade_clicked",
            "session_id": "growth_metrics_session",
            "timestamp": (now - timedelta(days=7, hours=-1)).isoformat(),
            "context": {"page": "/prompt/demo", "feature": "pytest_growth"},
            "metadata": {},
            "source": "pytest",
        },
        {
            "event_id": f"{event_base}_subscription",
            "event_name": "subscription_activated",
            "session_id": "growth_metrics_session",
            "timestamp": (now - timedelta(days=6)).isoformat(),
            "context": {"page": "/billing", "feature": "pytest_growth"},
            "metadata": {},
            "source": "pytest",
        },
    ]
    ingest = await async_client.post(
        "/api/v1/analytics/events",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"events": events},
    )
    assert ingest.status_code == 202

    dashboard = await async_client.get(
        "/api/v1/analytics/growth/dashboard?window_days=28",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert dashboard.status_code == 200
    payload = dashboard.json()

    assert payload["metrics"]["activation_rate"] >= 0
    assert payload["metrics"]["free_to_paid_conversion"] >= 0
    assert payload["funnel"]["steps"]
    assert payload["cohorts"]
    assert payload["experiments"]
    assert payload["rollout_flags"]

