from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_top_contributors_public(async_client):
    r = await async_client.get("/api/v1/contributors/top?limit=3")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
