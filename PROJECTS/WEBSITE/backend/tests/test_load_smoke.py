"""Lightweight concurrency smoke for hot paths (not a full load test)."""

from __future__ import annotations

import asyncio

import pytest


@pytest.mark.asyncio
async def test_health_under_concurrent_gets(async_client) -> None:
    results = await asyncio.gather(*[async_client.get("/health") for _ in range(40)])
    assert all(r.status_code == 200 for r in results)


@pytest.mark.asyncio
async def test_discovery_filters_under_concurrent_gets(async_client) -> None:
    results = await asyncio.gather(*[async_client.get("/api/v1/prompts/discovery-filters") for _ in range(15)])
    assert all(r.status_code == 200 for r in results)
