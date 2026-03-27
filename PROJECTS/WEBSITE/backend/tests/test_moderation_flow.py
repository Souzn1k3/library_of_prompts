"""Moderator queue, approve/reject, validation edge cases."""

from __future__ import annotations

import uuid

import pytest

from app.infrastructure.db.models import UserRole

from tests.helpers.db_users import set_user_role


async def _first_category_id(async_client) -> uuid.UUID:
    r = await async_client.get("/api/v1/categories")
    assert r.status_code == 200
    cats = r.json()
    assert isinstance(cats, list) and len(cats) > 0
    return uuid.UUID(cats[0]["id"])


def _submit_body() -> str:
    return "x" * 200


@pytest.mark.asyncio
async def test_moderator_approve_publishes_prompt(async_client, unique_email: str) -> None:
    cat_id = await _first_category_id(async_client)
    slug = f"mod-approve-{uuid.uuid4().hex[:12]}"

    author_reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "password123",
            "display_name": "Author",
        },
    )
    assert author_reg.status_code == 201
    author_token = author_reg.json()["access_token"]

    sub = await async_client.post(
        "/api/v1/contributions/submit",
        headers={"Authorization": f"Bearer {author_token}"},
        json={
            "slug": slug,
            "title": "Pending submission",
            "body": _submit_body(),
            "category_id": str(cat_id),
            "technique": "other",
        },
    )
    assert sub.status_code == 201
    prompt_id = sub.json()["id"]

    mod_email = f"mod_{uuid.uuid4().hex[:10]}@example.com"
    mod_reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": mod_email,
            "password": "password123",
            "display_name": "Moderator",
        },
    )
    assert mod_reg.status_code == 201
    await set_user_role(email=mod_email, role=UserRole.moderator)
    mod_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": mod_email, "password": "password123"},
    )
    mod_token = mod_login.json()["access_token"]

    q = await async_client.get(
        "/api/v1/moderation/queue",
        headers={"Authorization": f"Bearer {mod_token}"},
    )
    assert q.status_code == 200
    ids = {uuid.UUID(str(item["id"])) for item in q.json()}
    assert uuid.UUID(str(prompt_id)) in ids

    dec = await async_client.post(
        f"/api/v1/moderation/{prompt_id}/decision",
        headers={"Authorization": f"Bearer {mod_token}"},
        json={"action": "approve"},
    )
    assert dec.status_code == 204

    mine = await async_client.get(
        "/api/v1/users/me/submissions",
        headers={"Authorization": f"Bearer {author_token}"},
    )
    assert mine.status_code == 200
    rows = mine.json()
    match = next((r for r in rows if r["slug"] == slug), None)
    assert match is not None
    assert match["status"] == "published"
    assert match["moderation_state"] == "approved"


@pytest.mark.asyncio
async def test_moderator_reject_requires_reason(async_client, unique_email: str) -> None:
    cat_id = await _first_category_id(async_client)
    slug = f"mod-reject-{uuid.uuid4().hex[:12]}"

    author_reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "password123",
            "display_name": "Author2",
        },
    )
    author_token = author_reg.json()["access_token"]
    sub = await async_client.post(
        "/api/v1/contributions/submit",
        headers={"Authorization": f"Bearer {author_token}"},
        json={
            "slug": slug,
            "title": "Reject me",
            "body": _submit_body(),
            "category_id": str(cat_id),
            "technique": "other",
        },
    )
    prompt_id = sub.json()["id"]

    mod_email = f"mod_{uuid.uuid4().hex[:10]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": mod_email,
            "password": "password123",
            "display_name": "Mod2",
        },
    )
    await set_user_role(email=mod_email, role=UserRole.moderator)
    mod_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": mod_email, "password": "password123"},
    )
    mod_token = mod_login.json()["access_token"]

    bad = await async_client.post(
        f"/api/v1/moderation/{prompt_id}/decision",
        headers={"Authorization": f"Bearer {mod_token}"},
        json={"action": "reject", "reason": "   "},
    )
    assert bad.status_code == 400
    assert bad.json().get("code") == "moderation_reason_required"

    ok = await async_client.post(
        f"/api/v1/moderation/{prompt_id}/decision",
        headers={"Authorization": f"Bearer {mod_token}"},
        json={"action": "reject", "reason": "Does not meet quality bar."},
    )
    assert ok.status_code == 204

    mine = await async_client.get(
        "/api/v1/users/me/submissions",
        headers={"Authorization": f"Bearer {author_token}"},
    )
    match = next((r for r in mine.json() if r["slug"] == slug), None)
    assert match is not None
    assert match["moderation_state"] == "rejected"
    assert match.get("moderation_notes") == "Does not meet quality bar."


@pytest.mark.asyncio
async def test_cannot_moderate_non_pending_prompt(async_client, unique_email: str) -> None:
    cat_id = await _first_category_id(async_client)
    slug = f"mod-twice-{uuid.uuid4().hex[:12]}"

    author_reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "password123",
            "display_name": "Author3",
        },
    )
    author_token = author_reg.json()["access_token"]
    sub = await async_client.post(
        "/api/v1/contributions/submit",
        headers={"Authorization": f"Bearer {author_token}"},
        json={
            "slug": slug,
            "title": "Twice",
            "body": _submit_body(),
            "category_id": str(cat_id),
            "technique": "other",
        },
    )
    prompt_id = sub.json()["id"]

    mod_email = f"mod_{uuid.uuid4().hex[:10]}@example.com"
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": mod_email,
            "password": "password123",
            "display_name": "Mod3",
        },
    )
    await set_user_role(email=mod_email, role=UserRole.moderator)
    mod_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": mod_email, "password": "password123"},
    )
    assert mod_login.status_code == 200
    mod_token = mod_login.json()["access_token"]

    first = await async_client.post(
        f"/api/v1/moderation/{prompt_id}/decision",
        headers={"Authorization": f"Bearer {mod_token}"},
        json={"action": "approve"},
    )
    assert first.status_code == 204

    second = await async_client.post(
        f"/api/v1/moderation/{prompt_id}/decision",
        headers={"Authorization": f"Bearer {mod_token}"},
        json={"action": "approve"},
    )
    assert second.status_code == 400
    assert second.json().get("code") == "not_pending"
