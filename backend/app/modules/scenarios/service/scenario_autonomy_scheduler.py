from __future__ import annotations

import asyncio
from collections.abc import Callable
from time import monotonic

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.logging import get_logger
from app.modules.scenarios.service.scenario_autonomy_service import ScenarioAutonomyService


log = get_logger(__name__)


async def run_scenario_autonomy_scheduler(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    service_factory: Callable[[AsyncSession], ScenarioAutonomyService],
    interval_minutes: int,
) -> None:
    interval_seconds = max(60, int(interval_minutes) * 60)

    while True:
        started = monotonic()
        try:
            async with session_factory() as session:
                service = service_factory(session)
                await service.run_autonomous_cycle(
                    actor=None,
                    trigger="scheduler",
                    force=False,
                )
                await session.commit()
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("scenario_autonomy_scheduler_run_failed")

        elapsed = monotonic() - started
        sleep_for = max(5.0, interval_seconds - elapsed)
        await asyncio.sleep(sleep_for)
