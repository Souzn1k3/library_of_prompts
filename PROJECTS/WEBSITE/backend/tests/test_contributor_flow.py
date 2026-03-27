"""Contributor submission + my submissions API consistency."""

from __future__ import annotations

import uuid

import pytest


async def _first_category_id(async_client) -> uuid.UUID:
    r = await async_client.get("/api/v1/categories")
    assert r.status_code == 200
    cats = r.json()
    assert len(cats) > 0
    return uuid.UUID(cats[0]["id"])


@pytest.mark.asyncio
async def test_submission_lists_in_me_submissions(async_client, unique_email: str) -> None:
    cat_id = await _first_category_id(async_client)
    slug = f"contrib-{uuid.uuid4().hex[:12]}"

    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "password123",
            "display_name": "Contributor",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]

    sub = await async_client.post(
        "/api/v1/contributions/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "slug": slug,
            "title": "My prompt",
            "body": "y" * 200,
            "category_id": str(cat_id),
            "technique": "other",
        },
    )
    assert sub.status_code == 201
    body = sub.json()
    assert body["slug"] == slug
    assert body["moderation_state"] == "pending"

    mine = await async_client.get(
        "/api/v1/users/me/submissions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert mine.status_code == 200
    rows = mine.json()
    slugs = {r["slug"] for r in rows}
    assert slug in slugs
