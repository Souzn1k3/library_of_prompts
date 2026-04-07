from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import Request, Response

from app.config import Settings
from app.core.errors import NotFoundError
from app.core.tiers import can_view_restricted_category
from app.infrastructure.db.models import GuestScenarioRunUsage, PlanTier, PromptStatus, User, UserScenarioWorkspace
from app.modules.catalog.repository.prompt_repository import PromptRepository
from app.modules.scenarios.model.scenario import (
    ScenarioDemoRunStatusRead,
    ScenarioDemoRunTrackRead,
    ScenarioDemoRunTrackWrite,
)
from app.modules.scenarios.repository.scenario_demo_repository import ScenarioDemoRepository
from app.modules.scenarios.repository.scenario_workspace_repository import ScenarioWorkspaceRepository
from app.modules.scenarios.service.guest_session import (
    request_device_fingerprint_hash,
    get_or_set_guest_session_id,
    request_ip_hash,
    request_user_agent_hash,
)


class ScenarioDemoRunService:
    def __init__(
        self,
        *,
        prompt_repo: PromptRepository,
        workspace_repo: ScenarioWorkspaceRepository,
        demo_repo: ScenarioDemoRepository,
        settings: Settings,
    ) -> None:
        self._prompt_repo = prompt_repo
        self._workspace_repo = workspace_repo
        self._demo_repo = demo_repo
        self._settings = settings

    async def get_status(
        self,
        *,
        prompt_slug: str,
        viewer: User | None,
        request: Request,
        response: Response,
    ) -> ScenarioDemoRunStatusRead:
        prompt = await self._resolve_prompt(prompt_slug=prompt_slug, viewer=viewer)
        now = datetime.now(timezone.utc)
        return await self._build_status(
            viewer=viewer,
            prompt_id=prompt.id,
            prompt_slug=prompt.slug,
            request=request,
            response=response,
            now=now,
            mutate=False,
            task_input=None,
        )

    async def track_run(
        self,
        *,
        body: ScenarioDemoRunTrackWrite,
        viewer: User | None,
        request: Request,
        response: Response,
    ) -> ScenarioDemoRunTrackRead:
        prompt = await self._resolve_prompt(prompt_slug=body.prompt_slug, viewer=viewer)
        now = datetime.now(timezone.utc)
        baseline = await self._build_status(
            viewer=viewer,
            prompt_id=prompt.id,
            prompt_slug=prompt.slug,
            request=request,
            response=response,
            now=now,
            mutate=False,
            task_input=None,
        )
        if not baseline.allowed:
            return ScenarioDemoRunTrackRead(executed=False, status=baseline, workspace=None)

        status = await self._build_status(
            viewer=viewer,
            prompt_id=prompt.id,
            prompt_slug=prompt.slug,
            request=request,
            response=response,
            now=now,
            mutate=True,
            task_input=body.task_input,
        )
        return ScenarioDemoRunTrackRead(executed=True, status=status, workspace=None)

    async def _resolve_prompt(self, *, prompt_slug: str, viewer: User | None):
        prompt = await self._prompt_repo.get_by_slug(prompt_slug)
        if prompt is None or prompt.status != PromptStatus.published:
            raise NotFoundError("prompt", prompt_slug)
        if (
            prompt.category
            and prompt.category.is_restricted
            and (viewer is None or not can_view_restricted_category(viewer))
        ):
            raise NotFoundError("prompt", prompt_slug)
        return prompt

    async def _build_status(
        self,
        *,
        viewer: User | None,
        prompt_id,
        prompt_slug: str,
        request: Request,
        response: Response,
        now: datetime,
        mutate: bool,
        task_input: str | None,
    ) -> ScenarioDemoRunStatusRead:
        free_cap = int(self._settings.scenario_free_demo_run_cap)
        upgrade_hint = "Unlock PRO to run this scenario without demo limits."

        if viewer is not None:
            return await self._auth_status(
                viewer=viewer,
                prompt_id=prompt_id,
                prompt_slug=prompt_slug,
                now=now,
                free_cap=free_cap,
                mutate=mutate,
                task_input=task_input,
                upgrade_hint=upgrade_hint,
            )

        return await self._guest_status(
            prompt_id=prompt_id,
            prompt_slug=prompt_slug,
            request=request,
            response=response,
            now=now,
            free_cap=free_cap,
            mutate=mutate,
            upgrade_hint=upgrade_hint,
        )

    async def _auth_status(
        self,
        *,
        viewer: User,
        prompt_id,
        prompt_slug: str,
        now: datetime,
        free_cap: int,
        mutate: bool,
        task_input: str | None,
        upgrade_hint: str,
    ) -> ScenarioDemoRunStatusRead:
        entry = await self._workspace_repo.get_workspace_entry(user_id=viewer.id, prompt_id=prompt_id)
        used_runs = int(entry.run_count) if entry is not None else 0
        is_pro = viewer.plan_tier != PlanTier.free

        if is_pro:
            if mutate:
                entry = await self._ensure_workspace_entry(entry=entry, viewer=viewer, prompt_id=prompt_id, now=now)
                entry.run_count = int(entry.run_count) + 1
                entry.last_run_at = now
                entry.last_opened_at = entry.last_opened_at or now
                entry.last_used_at = now
                clean_task = (task_input or "").strip()
                if clean_task:
                    entry.unfinished_task = clean_task
                await self._workspace_repo.save_workspace_entry(entry)
                used_runs = int(entry.run_count)

            return ScenarioDemoRunStatusRead(
                prompt_slug=prompt_slug,
                is_authenticated=True,
                is_pro=True,
                free_cap=None,
                used_runs=used_runs,
                remaining_runs=None,
                cap_reached=False,
                allowed=True,
                reason=None,
                upgrade_hint=None,
                guest_session_id=None,
            )

        cap_reached = used_runs >= free_cap
        allowed = not cap_reached
        reason = "free_demo_cap_reached" if cap_reached else None

        if mutate and allowed:
            entry = await self._ensure_workspace_entry(entry=entry, viewer=viewer, prompt_id=prompt_id, now=now)
            entry.run_count = int(entry.run_count) + 1
            entry.last_run_at = now
            entry.last_opened_at = entry.last_opened_at or now
            entry.last_used_at = now
            clean_task = (task_input or "").strip()
            if clean_task:
                entry.unfinished_task = clean_task
            await self._workspace_repo.save_workspace_entry(entry)
            used_runs = int(entry.run_count)
            cap_reached = used_runs >= free_cap
            allowed = not cap_reached
            reason = "free_demo_cap_reached" if cap_reached else None

        remaining = max(free_cap - used_runs, 0)
        return ScenarioDemoRunStatusRead(
            prompt_slug=prompt_slug,
            is_authenticated=True,
            is_pro=False,
            free_cap=free_cap,
            used_runs=used_runs,
            remaining_runs=remaining,
            cap_reached=cap_reached,
            allowed=allowed,
            reason=reason,
            upgrade_hint=upgrade_hint if cap_reached else None,
            guest_session_id=None,
        )

    async def _guest_status(
        self,
        *,
        prompt_id,
        prompt_slug: str,
        request: Request,
        response: Response,
        now: datetime,
        free_cap: int,
        mutate: bool,
        upgrade_hint: str,
    ) -> ScenarioDemoRunStatusRead:
        guest_id = get_or_set_guest_session_id(request=request, response=response, settings=self._settings)
        usage = await self._demo_repo.get_guest_run_usage(guest_id=guest_id, prompt_id=prompt_id)
        used_runs = int(usage.run_count) if usage is not None else 0

        ip_hash = request_ip_hash(request)
        ua_hash = request_user_agent_hash(request)
        fingerprint_hash = request_device_fingerprint_hash(request)
        anti_abuse_since = now - timedelta(hours=int(self._settings.scenario_guest_anti_abuse_window_hours))
        ip_daily_runs = await self._demo_repo.sum_guest_runs_for_prompt_ip_since(
            prompt_id=prompt_id,
            ip_hash=ip_hash,
            since=anti_abuse_since,
        )
        fingerprint_daily_runs = await self._demo_repo.sum_guest_runs_for_prompt_fingerprint_since(
            prompt_id=prompt_id,
            fingerprint_hash=fingerprint_hash,
            since=anti_abuse_since,
        )
        distinct_guest_sessions = await self._demo_repo.count_distinct_guest_sessions_for_prompt_ip_since(
            prompt_id=prompt_id,
            ip_hash=ip_hash,
            since=anti_abuse_since,
        )
        ip_cap_reached = ip_daily_runs >= int(self._settings.scenario_guest_ip_daily_prompt_cap)
        fingerprint_cap_reached = (
            fingerprint_daily_runs >= int(self._settings.scenario_guest_fingerprint_daily_prompt_cap)
        )
        rotation_detected = (
            distinct_guest_sessions >= int(self._settings.scenario_guest_ip_rotation_prompt_cap)
        )

        cap_reached = used_runs >= free_cap
        allowed = not cap_reached and not ip_cap_reached and not fingerprint_cap_reached and not rotation_detected
        reason: str | None = None
        if rotation_detected:
            reason = "guest_ip_rotation_detected"
        elif ip_cap_reached:
            reason = "guest_ip_prompt_daily_cap_reached"
        elif fingerprint_cap_reached:
            reason = "guest_fingerprint_prompt_daily_cap_reached"
        elif cap_reached:
            reason = "free_demo_cap_reached"

        if mutate and allowed:
            if usage is None:
                usage = GuestScenarioRunUsage(
                    guest_id=guest_id,
                    prompt_id=prompt_id,
                    run_count=0,
                    created_at=now,
                    updated_at=now,
                )
                await self._demo_repo.create_guest_run_usage(usage)

            usage.run_count = int(usage.run_count) + 1
            usage.last_run_at = now
            usage.last_ip_hash = ip_hash
            usage.last_user_agent_hash = ua_hash
            usage.last_fingerprint_hash = fingerprint_hash
            await self._demo_repo.save_guest_run_usage(usage)
            used_runs = int(usage.run_count)
            ip_daily_runs += 1
            fingerprint_daily_runs += 1
            cap_reached = used_runs >= free_cap
            ip_cap_reached = ip_daily_runs >= int(self._settings.scenario_guest_ip_daily_prompt_cap)
            fingerprint_cap_reached = (
                fingerprint_daily_runs >= int(self._settings.scenario_guest_fingerprint_daily_prompt_cap)
            )
            allowed = not cap_reached and not ip_cap_reached and not fingerprint_cap_reached and not rotation_detected
            if cap_reached:
                reason = "free_demo_cap_reached"
            elif rotation_detected:
                reason = "guest_ip_rotation_detected"
            elif ip_cap_reached:
                reason = "guest_ip_prompt_daily_cap_reached"
            elif fingerprint_cap_reached:
                reason = "guest_fingerprint_prompt_daily_cap_reached"
            else:
                reason = None

        remaining = max(free_cap - used_runs, 0)
        return ScenarioDemoRunStatusRead(
            prompt_slug=prompt_slug,
            is_authenticated=False,
            is_pro=False,
            free_cap=free_cap,
            used_runs=used_runs,
            remaining_runs=remaining,
            cap_reached=cap_reached or ip_cap_reached or fingerprint_cap_reached or rotation_detected,
            allowed=allowed,
            reason=reason,
            upgrade_hint=upgrade_hint if (cap_reached or ip_cap_reached or fingerprint_cap_reached or rotation_detected) else None,
            guest_session_id=guest_id,
        )

    async def _ensure_workspace_entry(
        self,
        *,
        entry: UserScenarioWorkspace | None,
        viewer: User,
        prompt_id,
        now: datetime,
    ) -> UserScenarioWorkspace:
        if entry is not None:
            return entry

        created = UserScenarioWorkspace(
            user_id=viewer.id,
            prompt_id=prompt_id,
            is_saved=False,
            run_count=0,
            copy_count=0,
            share_count=0,
            last_used_at=now,
            created_at=now,
            updated_at=now,
        )
        return await self._workspace_repo.create_workspace_entry(created)
