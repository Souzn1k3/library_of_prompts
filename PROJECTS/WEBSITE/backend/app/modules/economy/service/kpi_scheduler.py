from __future__ import annotations

import asyncio
from time import monotonic

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.logging import get_logger
from app.modules.economy.repository.kpi_repository import EconomyKpiRepository
from app.modules.economy.service.kpi_service import EconomyKpiService


log = get_logger(__name__)


async def run_economy_kpi_scheduler(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    interval_minutes: int,
    lookback_days: int,
    include_today: bool = True,
) -> None:
    interval_seconds = max(60, int(interval_minutes) * 60)
    horizon = max(1, int(lookback_days))

    while True:
        started = monotonic()
        try:
            async with session_factory() as session:
                service = EconomyKpiService(EconomyKpiRepository(session))
                await service.aggregate_recent_days(
                    lookback_days=horizon,
                    include_today=include_today,
                )
                await session.commit()
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("economy_kpi_scheduler_run_failed")

        elapsed = monotonic() - started
        sleep_for = max(5.0, interval_seconds - elapsed)
        await asyncio.sleep(sleep_for)
