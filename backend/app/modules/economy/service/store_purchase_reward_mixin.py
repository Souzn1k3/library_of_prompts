from __future__ import annotations

from datetime import datetime, timedelta
import uuid

from app.infrastructure.db.models import CurrencyTransactionType, StoreItem, StoreItemKind, User
from app.modules.analytics.model.analytics import AnalyticsEventName
from app.modules.economy.config.tuning import (
    DEFAULT_BOOST_MISSIONS,
    DEFAULT_BOOST_PCT,
    FIRST_PURCHASE_BONUS_LUMENS,
    LOCKED_CASHBACK_RATE,
    LOCKED_CASHBACK_UNLOCK_WINDOW_HOURS,
    SECOND_PURCHASE_CHALLENGE_BOOST_MISSIONS,
    SECOND_PURCHASE_CHALLENGE_BOOST_PCT,
    SECOND_PURCHASE_CHALLENGE_REWARD,
    SECOND_PURCHASE_CHALLENGE_WINDOW_HOURS,
)
from app.modules.economy.model.store import StoreRewardRead


class StorePurchaseRewardMixin:
    async def _grant_first_purchase_bonus_if_needed(
        self,
        *,
        user: User,
        item: StoreItem,
        had_purchase_before: bool,
        purchase_metadata: dict[str, object],
        now: datetime,
    ) -> StoreRewardRead | None:
        if had_purchase_before:
            return None
        await self._wallet_repo.adjust_balance(
            user_id=user.id,
            amount=FIRST_PURCHASE_BONUS_LUMENS,
            reason=CurrencyTransactionType.first_purchase_bonus,
            context=f"store:first_purchase:{item.slug}",
            source_id=item.id,
            metadata={"item_slug": item.slug, "item_title": item.title},
            now=now,
        )
        purchase_metadata["first_purchase_bonus_amount"] = FIRST_PURCHASE_BONUS_LUMENS
        return self._rewards.first_purchase_reward(FIRST_PURCHASE_BONUS_LUMENS)

    async def _create_locked_cashback_reward(
        self,
        *,
        user: User,
        item: StoreItem,
        purchase_id: uuid.UUID,
        now: datetime,
    ) -> tuple[StoreRewardRead | None, int]:
        locked_cashback_reward: StoreRewardRead | None = None
        cashback_amount = int(item.price * LOCKED_CASHBACK_RATE)
        if cashback_amount <= 0:
            return locked_cashback_reward, cashback_amount

        unlock_by = now + timedelta(hours=LOCKED_CASHBACK_UNLOCK_WINDOW_HOURS)
        locked_reward = await self._wallet_repo.create_locked_cashback(
            user_id=user.id,
            amount=cashback_amount,
            source_purchase_id=purchase_id,
            unlock_by=unlock_by,
            metadata={"item_slug": item.slug, "item_title": item.title},
        )
        if locked_reward is not None:
            await self._wallet_repo.adjust_balance(
                user_id=user.id,
                amount=0,
                reason=CurrencyTransactionType.cashback_locked,
                context=f"cashback_locked:{locked_reward.id}",
                source_id=locked_reward.id,
                metadata={
                    "locked_reward_id": str(locked_reward.id),
                    "amount": cashback_amount,
                    "unlock_by": unlock_by.isoformat(),
                },
                now=now,
            )
            locked_cashback_reward = self._rewards.locked_cashback_reward(cashback_amount)
        return locked_cashback_reward, cashback_amount

    async def _apply_second_purchase_challenge(
        self,
        *,
        user: User,
        item: StoreItem,
        purchase_id: uuid.UUID,
        now: datetime,
        purchase_metadata: dict[str, object],
        experiment_meta: dict[str, object],
    ) -> tuple[StoreRewardRead | None, str]:
        second_purchase_challenge_reward: StoreRewardRead | None = None
        challenge_state = await self._wallet_repo.track_second_purchase_challenge(user_id=user.id, now=now)
        if challenge_state == "started":
            purchase_metadata["second_purchase_challenge_expires_at"] = (
                now + timedelta(hours=SECOND_PURCHASE_CHALLENGE_WINDOW_HOURS)
            ).isoformat()
            if self._analytics is not None:
                await self._analytics.record_server_event(
                    event_name=AnalyticsEventName.second_purchase_challenge_started,
                    user_id=user.id,
                    metadata={
                        **experiment_meta,
                        "purchase_id": str(purchase_id),
                        "item_slug": item.slug,
                        "expires_at": purchase_metadata["second_purchase_challenge_expires_at"],
                    },
                    context_page="/api/v1/store",
                    context_feature="second_purchase_challenge",
                    event_id=f"second_purchase_challenge_started:{user.id}:{purchase_id}",
                )
        if challenge_state == "completed":
            await self._wallet_repo.adjust_balance(
                user_id=user.id,
                amount=SECOND_PURCHASE_CHALLENGE_REWARD,
                reason=CurrencyTransactionType.rank_bonus,
                context=f"second_purchase_challenge:{purchase_id}",
                source_id=purchase_id,
                metadata={"challenge": "second_purchase", "item_slug": item.slug},
                now=now,
            )
            await self._wallet_repo.grant_active_boost(
                user_id=user.id,
                source_purchase_id=purchase_id,
                boost_percent=SECOND_PURCHASE_CHALLENGE_BOOST_PCT,
                missions_total=SECOND_PURCHASE_CHALLENGE_BOOST_MISSIONS,
                metadata={"item_slug": "challenge_boost", "source": "second_purchase_challenge"},
            )
            second_purchase_challenge_reward = self._rewards.second_purchase_challenge_reward(
                SECOND_PURCHASE_CHALLENGE_REWARD
            )
            if self._analytics is not None:
                await self._analytics.record_server_event(
                    event_name=AnalyticsEventName.second_purchase_challenge_completed,
                    user_id=user.id,
                    metadata={
                        **experiment_meta,
                        "purchase_id": str(purchase_id),
                        "item_slug": item.slug,
                        "reward_lmn": SECOND_PURCHASE_CHALLENGE_REWARD,
                        "reward_boost_pct": SECOND_PURCHASE_CHALLENGE_BOOST_PCT,
                        "reward_boost_missions": SECOND_PURCHASE_CHALLENGE_BOOST_MISSIONS,
                    },
                    context_page="/api/v1/store",
                    context_feature="second_purchase_challenge",
                    event_id=f"second_purchase_challenge_completed:{user.id}:{purchase_id}",
                )
        return second_purchase_challenge_reward, challenge_state

    async def _apply_item_kind_rewards(
        self,
        *,
        user: User,
        item: StoreItem,
        purchase_id: uuid.UUID,
        now: datetime,
    ) -> None:
        if item.kind == StoreItemKind.boost:
            await self._wallet_repo.grant_active_boost(
                user_id=user.id,
                source_purchase_id=purchase_id,
                boost_percent=int((item.meta or {}).get("boost_pct", DEFAULT_BOOST_PCT)),
                missions_total=int((item.meta or {}).get("boost_missions", DEFAULT_BOOST_MISSIONS)),
                metadata={"item_slug": item.slug, "item_title": item.title},
            )
