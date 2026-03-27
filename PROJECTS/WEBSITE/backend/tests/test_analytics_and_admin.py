from __future__ import annotations

from datetime import datetime, timezone

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
async def test_analytics_recent_requires_admin(async_client, unique_email: str):
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "password123",
            "display_name": "User",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]

    r = await async_client.get(
        "/api/v1/analytics/events/recent",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_analytics_recent_admin_ok(async_client, unique_email: str):
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "password123",
            "display_name": "Admin Test",
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

    r = await async_client.get(
        "/api/v1/analytics/events/recent?limit=5",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_analytics_ingest_accepts_event(async_client, unique_email: str):
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "password123",
            "display_name": "A",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    payload = {
        "event": {
            "event_id": f"pytest_evt_{unique_email[:8]}",
            "event_name": "page_viewed",
            "session_id": "pytest_session",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context": {"page": "/test", "feature": "pytest"},
            "metadata": {},
            "source": "pytest",
        }
    }
    r = await async_client.post(
        "/api/v1/analytics/events",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert r.status_code == 202
    body = r.json()
    assert body.get("ingested", 0) >= 0
