from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Request, Response

from app.config import Settings
from app.core.errors import AppError
from app.infrastructure.db.models import CurrencyTransactionType, ScenarioGameTokenClaim, ScenarioGameTokenEvent, User
from app.modules.economy.service.wallet_service import WalletService
from app.modules.scenarios.model.scenario import (
    ScenarioGameClaimRead,
    ScenarioGameClaimWrite,
    ScenarioGameEarnRead,
    ScenarioGameEarnWrite,
    ScenarioGameStateRead,
)
from app.modules.scenarios.repository.scenario_demo_repository import ScenarioDemoRepository
from app.modules.scenarios.service.guest_session import (
    get_or_set_guest_session_id,
    request_device_fingerprint_hash,
    request_ip_hash,
    request_user_agent_hash,
)

WEB_DEMO_REWARD_MATRIX: dict[str, dict[int, int]] = {
    "challenge-1": {0: 1, 1: 6, 2: 2},
    "challenge-2": {0: 1, 1: 6, 2: 2},
    "challenge-3": {0: 2, 1: 6, 2: 1},
}


class ScenarioGameService:
    def __init__(
        self,
        *,
        repo: ScenarioDemoRepository,
        wallet: WalletService,
        settings: Settings,
    ) -> None:
        self._repo = repo
        self._wallet = wallet
        self._settings = settings

    async def get_state(
        self,
        *,
        viewer: User | None,
        request: Request,
        response: Response,
    ) -> ScenarioGameStateRead:
        guest_id = get_or_set_guest_session_id(request=request, response=response, settings=self._settings)
        now = datetime.now(timezone.utc)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        daily_cap = int(self._settings.web_demo_game_daily_token_cap)
        ip_hash = request_ip_hash(request)
        fingerprint_hash = request_device_fingerprint_hash(request)

        earned_today = await self._repo.sum_game_tokens_for_actor_since(
            user_id=viewer.id if viewer is not None else None,
            guest_id=guest_id if viewer is None else guest_id,
            since=day_start,
        )
        pending_tokens = await self._repo.sum_game_pending_tokens(
            user_id=viewer.id if viewer is not None else None,
            guest_id=guest_id if viewer is None else guest_id,
            include_guest_for_user=viewer is not None,
        )
        claimed_today = (
            await self._repo.sum_game_claimed_tokens_for_user_since(user_id=viewer.id, since=day_start)
            if viewer is not None
            else 0
        )
        daily_cap_remaining = max(daily_cap - earned_today, 0)
        if viewer is None:
            guest_ip_earned_today = await self._repo.sum_game_tokens_for_guest_ip_since(
                ip_hash=ip_hash,
                since=day_start,
            )
            guest_fingerprint_earned_today = await self._repo.sum_game_tokens_for_guest_fingerprint_since(
                fingerprint_hash=fingerprint_hash,
                since=day_start,
            )
            guest_ip_remaining = max(
                int(self._settings.web_demo_game_guest_ip_daily_token_cap) - guest_ip_earned_today,
                0,
            )
            guest_fingerprint_remaining = max(
                int(self._settings.web_demo_game_guest_fingerprint_daily_token_cap) - guest_fingerprint_earned_today,
                0,
            )
            daily_cap_remaining = min(daily_cap_remaining, guest_ip_remaining, guest_fingerprint_remaining)

        return ScenarioGameStateRead(
            pending_tokens=pending_tokens,
            claimable_tokens=pending_tokens,
            claimed_tokens_today=claimed_today,
            daily_cap=daily_cap,
            daily_cap_remaining=daily_cap_remaining,
            cooldown_minutes=int(self._settings.web_demo_game_challenge_cooldown_minutes),
            needs_auth_to_claim=True,
        )

    async def earn(
        self,
        *,
        body: ScenarioGameEarnWrite,
        viewer: User | None,
        request: Request,
        response: Response,
    ) -> ScenarioGameEarnRead:
        guest_id = get_or_set_guest_session_id(request=request, response=response, settings=self._settings)
        now = datetime.now(timezone.utc)
        daily_cap = int(self._settings.web_demo_game_daily_token_cap)
        cooldown = timedelta(minutes=int(self._settings.web_demo_game_challenge_cooldown_minutes))
        ip_hash = request_ip_hash(request)
        user_agent_hash = request_user_agent_hash(request)
        fingerprint_hash = request_device_fingerprint_hash(request)

        reward_tokens = self._reward_for(challenge_id=body.challenge_id, choice_index=body.choice_index)
        if reward_tokens is None:
            raise AppError(
                code="invalid_demo_game_choice",
                message="The selected challenge choice is invalid.",
                status_code=400,
            )

        existing = await self._repo.get_game_event_by_event_id(event_id=body.event_id)
        if existing is not None:
            pending_tokens = await self._repo.sum_game_pending_tokens(
                user_id=viewer.id if viewer is not None else None,
                guest_id=guest_id if viewer is None else guest_id,
                include_guest_for_user=viewer is not None,
            )
            day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            earned_today = await self._repo.sum_game_tokens_for_actor_since(
                user_id=viewer.id if viewer is not None else None,
                guest_id=guest_id if viewer is None else guest_id,
                since=day_start,
            )
            return ScenarioGameEarnRead(
                accepted=False,
                reason="duplicate_event_id",
                reward_tokens=0,
                pending_tokens=pending_tokens,
                daily_cap_remaining=max(daily_cap - earned_today, 0),
                cooldown_seconds=None,
            )

        latest = await self._repo.get_latest_game_event_for_actor_challenge(
            user_id=viewer.id if viewer is not None else None,
            guest_id=guest_id if viewer is None else guest_id,
            challenge_id=body.challenge_id,
        )
        if latest is not None and (now - latest.occurred_at) < cooldown:
            pending_tokens = await self._repo.sum_game_pending_tokens(
                user_id=viewer.id if viewer is not None else None,
                guest_id=guest_id if viewer is None else guest_id,
                include_guest_for_user=viewer is not None,
            )
            day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            earned_today = await self._repo.sum_game_tokens_for_actor_since(
                user_id=viewer.id if viewer is not None else None,
                guest_id=guest_id if viewer is None else guest_id,
                since=day_start,
            )
            seconds_left = int((cooldown - (now - latest.occurred_at)).total_seconds())
            return ScenarioGameEarnRead(
                accepted=False,
                reason="challenge_cooldown_active",
                reward_tokens=0,
                pending_tokens=pending_tokens,
                daily_cap_remaining=max(daily_cap - earned_today, 0),
                cooldown_seconds=max(seconds_left, 0),
            )

        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        earned_today = await self._repo.sum_game_tokens_for_actor_since(
            user_id=viewer.id if viewer is not None else None,
            guest_id=guest_id if viewer is None else guest_id,
            since=day_start,
        )
        if earned_today + reward_tokens > daily_cap:
            pending_tokens = await self._repo.sum_game_pending_tokens(
                user_id=viewer.id if viewer is not None else None,
                guest_id=guest_id if viewer is None else guest_id,
                include_guest_for_user=viewer is not None,
            )
            return ScenarioGameEarnRead(
                accepted=False,
                reason="daily_cap_reached",
                reward_tokens=0,
                pending_tokens=pending_tokens,
                daily_cap_remaining=max(daily_cap - earned_today, 0),
                cooldown_seconds=None,
            )

        if viewer is None:
            guest_ip_earned_today = await self._repo.sum_game_tokens_for_guest_ip_since(
                ip_hash=ip_hash,
                since=day_start,
            )
            if guest_ip_earned_today + reward_tokens > int(self._settings.web_demo_game_guest_ip_daily_token_cap):
                pending_tokens = await self._repo.sum_game_pending_tokens(
                    user_id=None,
                    guest_id=guest_id,
                    include_guest_for_user=False,
                )
                return ScenarioGameEarnRead(
                    accepted=False,
                    reason="guest_ip_daily_cap_reached",
                    reward_tokens=0,
                    pending_tokens=pending_tokens,
                    daily_cap_remaining=max(
                        int(self._settings.web_demo_game_guest_ip_daily_token_cap) - guest_ip_earned_today,
                        0,
                    ),
                    cooldown_seconds=None,
                )

            guest_fingerprint_earned_today = await self._repo.sum_game_tokens_for_guest_fingerprint_since(
                fingerprint_hash=fingerprint_hash,
                since=day_start,
            )
            if guest_fingerprint_earned_today + reward_tokens > int(
                self._settings.web_demo_game_guest_fingerprint_daily_token_cap
            ):
                pending_tokens = await self._repo.sum_game_pending_tokens(
                    user_id=None,
                    guest_id=guest_id,
                    include_guest_for_user=False,
                )
                return ScenarioGameEarnRead(
                    accepted=False,
                    reason="guest_fingerprint_daily_cap_reached",
                    reward_tokens=0,
                    pending_tokens=pending_tokens,
                    daily_cap_remaining=max(
                        int(self._settings.web_demo_game_guest_fingerprint_daily_token_cap)
                        - guest_fingerprint_earned_today,
                        0,
                    ),
                    cooldown_seconds=None,
                )

            window_minutes = int(self._settings.web_demo_game_guest_fingerprint_window_minutes)
            window_since = now - timedelta(minutes=window_minutes)
            recent_event_count = await self._repo.count_game_events_for_guest_fingerprint_since(
                fingerprint_hash=fingerprint_hash,
                since=window_since,
            )
            if recent_event_count >= int(self._settings.web_demo_game_guest_fingerprint_window_event_cap):
                pending_tokens = await self._repo.sum_game_pending_tokens(
                    user_id=None,
                    guest_id=guest_id,
                    include_guest_for_user=False,
                )
                return ScenarioGameEarnRead(
                    accepted=False,
                    reason="guest_rate_limited",
                    reward_tokens=0,
                    pending_tokens=pending_tokens,
                    daily_cap_remaining=max(daily_cap - earned_today, 0),
                    cooldown_seconds=window_minutes * 60,
                )

        event = ScenarioGameTokenEvent(
            event_id=body.event_id,
            source="web_demo",
            user_id=viewer.id if viewer is not None else None,
            guest_id=guest_id if viewer is None else guest_id,
            challenge_id=body.challenge_id,
            choice_index=body.choice_index,
            reward_tokens=reward_tokens,
            status="pending",
            ip_hash=ip_hash,
            user_agent_hash=user_agent_hash,
            fingerprint_hash=fingerprint_hash,
            occurred_at=now,
            created_at=now,
            meta={"mode": "demo_game"},
        )
        await self._repo.create_game_event(event)

        pending_tokens = await self._repo.sum_game_pending_tokens(
            user_id=viewer.id if viewer is not None else None,
            guest_id=guest_id if viewer is None else guest_id,
            include_guest_for_user=viewer is not None,
        )
        return ScenarioGameEarnRead(
            accepted=True,
            reason="accepted",
            reward_tokens=reward_tokens,
            pending_tokens=pending_tokens,
            daily_cap_remaining=max(daily_cap - (earned_today + reward_tokens), 0),
            cooldown_seconds=None,
        )

    async def claim(
        self,
        *,
        body: ScenarioGameClaimWrite,
        viewer: User | None,
        request: Request,
        response: Response,
    ) -> ScenarioGameClaimRead:
        if viewer is None:
            raise AppError(
                code="not_authenticated",
                message="Please log in to claim demo game tokens.",
                status_code=401,
            )

        guest_id = get_or_set_guest_session_id(request=request, response=response, settings=self._settings)
        claim_id = (body.claim_id or uuid.uuid4().hex).strip()
        if not claim_id:
            claim_id = uuid.uuid4().hex

        existing_claim = await self._repo.get_game_claim_by_claim_id(claim_id=claim_id)
        if existing_claim is not None:
            if existing_claim.user_id != viewer.id:
                raise AppError(
                    code="claim_id_conflict",
                    message="Claim id is already used.",
                    status_code=409,
                )
            return ScenarioGameClaimRead(
                claim_id=existing_claim.claim_id,
                applied=bool(existing_claim.claimed_tokens > 0),
                claimed_tokens=int(existing_claim.claimed_tokens),
                pending_tokens_after=int(existing_claim.pending_tokens_after),
                balance_after=existing_claim.balance_after,
            )

        pending_events = await self._repo.list_pending_game_events_for_claim(
            user_id=viewer.id,
            guest_id=guest_id,
        )
        pending_total = int(sum(max(int(event.reward_tokens), 0) for event in pending_events))
        now = datetime.now(timezone.utc)

        if pending_total <= 0:
            claim = ScenarioGameTokenClaim(
                claim_id=claim_id,
                user_id=viewer.id,
                guest_id=guest_id,
                source="web_demo",
                status="empty",
                claimed_tokens=0,
                pending_tokens_after=0,
                balance_after=None,
                meta={"event_count": 0},
                created_at=now,
            )
            await self._repo.create_game_claim(claim)
            return ScenarioGameClaimRead(
                claim_id=claim.claim_id,
                applied=False,
                claimed_tokens=0,
                pending_tokens_after=0,
                balance_after=None,
            )

        await self._wallet.ensure_wallet(viewer.id)
        await self._wallet.adjust(
            user_id=viewer.id,
            amount=pending_total,
            reason=CurrencyTransactionType.surprise_reward,
            context=f"web_demo_claim:{claim_id}",
            metadata={
                "source": "web_demo_game",
                "claim_id": claim_id,
                "event_count": len(pending_events),
            },
            now=now,
        )
        wallet = await self._wallet.get_wallet(viewer, limit=1)

        for event in pending_events:
            event.status = "claimed"
            event.claimed_at = now
            event.claim_id = claim_id
            event.user_id = viewer.id
            await self._repo.save_game_event(event)

        claim = ScenarioGameTokenClaim(
            claim_id=claim_id,
            user_id=viewer.id,
            guest_id=guest_id,
            source="web_demo",
            status="completed",
            claimed_tokens=pending_total,
            pending_tokens_after=0,
            balance_after=int(wallet.balance),
            meta={"event_count": len(pending_events)},
            created_at=now,
        )
        await self._repo.create_game_claim(claim)

        return ScenarioGameClaimRead(
            claim_id=claim.claim_id,
            applied=True,
            claimed_tokens=pending_total,
            pending_tokens_after=0,
            balance_after=int(wallet.balance),
        )

    @staticmethod
    def _reward_for(*, challenge_id: str, choice_index: int) -> int | None:
        return WEB_DEMO_REWARD_MATRIX.get(challenge_id, {}).get(choice_index)
