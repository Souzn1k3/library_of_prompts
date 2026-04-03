import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.infrastructure.db.models import (
    BoostStatus,
    CurrencyTransaction,
    CurrencyTransactionType,
    LockedRewardStatus,
    MissionCompletionEvent,
    MissionRewardType,
    PurchaseStatus,
    StoreItem,
    User,
    UserActiveBoost,
    UserCurrencyBalance,
    UserLockedReward,
    UserPurchase,
)
from app.modules.economy.config.tuning import (
    CATCHUP_BOOST_EXPIRY_HOURS,
    CATCHUP_BOOST_PCT,
    HOARDER_BALANCE_THRESHOLD,
    HOARDER_SPEND_RECENT_MAX,
    LOCKED_CASHBACK_REQUIRED_MISSIONS,
    RANK_THRESHOLDS,
    SECOND_PURCHASE_CHALLENGE_WINDOW_HOURS,
    SEGMENT_MISSION_LOOKBACK_HOURS,
    SEGMENT_SPEND_LOOKBACK_DAYS,
    SPENDER_SPEND_RECENT_MIN,
    SPEND_STREAK_MULTIPLIERS,
)


class WalletRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _is_sqlite(self) -> bool:
        bind = self._session.bind
        return bool(bind and bind.dialect.name == "sqlite")

    def _insert(self, model):
        return sqlite_insert(model) if self._is_sqlite() else pg_insert(model)

    def _rank_level(self, points: int) -> int:
        level = 1
        for index, threshold in enumerate(RANK_THRESHOLDS, start=1):
            if points >= threshold:
                level = index
            else:
                break
        return level

    def rank_next_threshold(self, level: int) -> int:
        index = max(1, level)
        if index >= len(RANK_THRESHOLDS):
            return RANK_THRESHOLDS[-1]
        return RANK_THRESHOLDS[index]

    def spend_streak_multiplier(self, streak_days: int) -> float:
        key = max(1, int(streak_days))
        if key >= 4:
            return SPEND_STREAK_MULTIPLIERS[4]
        return SPEND_STREAK_MULTIPLIERS[key]

    def _recompute_rank(self, row: UserCurrencyBalance) -> tuple[int, int]:
        points = int(row.total_earned + int(row.total_spent * 0.7))
        row.rank_points = points
        row.rank_level = self._rank_level(points)
        return row.rank_points, row.rank_level

    async def ensure_balance_row(self, user_id: uuid.UUID, *, for_update: bool = False) -> UserCurrencyBalance:
        stmt = select(UserCurrencyBalance).where(UserCurrencyBalance.user_id == user_id)
        if for_update and not self._is_sqlite():
            stmt = stmt.with_for_update()
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row:
            self._recompute_rank(row)
            return row

        user_row = await self._session.execute(select(User.mission_credits).where(User.id == user_id))
        starting_balance = int(user_row.scalar_one_or_none() or 0)
        insert_stmt = (
            self._insert(UserCurrencyBalance)
            .values(
                user_id=user_id,
                balance=starting_balance,
                total_earned=max(starting_balance, 0),
                total_spent=max(-starting_balance, 0),
                rank_points=max(starting_balance, 0),
                rank_level=1,
            )
            .on_conflict_do_nothing(index_elements=["user_id"])
        )
        await self._session.execute(insert_stmt)
        row = (await self._session.execute(stmt)).scalar_one()
        self._recompute_rank(row)
        return row

    async def get_balance_row(self, user_id: uuid.UUID, *, for_update: bool = False) -> UserCurrencyBalance:
        return await self.ensure_balance_row(user_id, for_update=for_update)

    async def adjust_balance(
        self,
        *,
        user_id: uuid.UUID,
        amount: int,
        reason: CurrencyTransactionType,
        context: str | None = None,
        source_id: uuid.UUID | None = None,
        metadata: dict | None = None,
        now: datetime | None = None,
    ) -> CurrencyTransaction:
        if amount == 0 and reason != CurrencyTransactionType.cashback_locked:
            raise AppError(
                code="invalid_amount",
                message="Amount must be non-zero.",
                status_code=400,
            )
        now = now or datetime.now(timezone.utc)
        balance_row = await self.ensure_balance_row(user_id, for_update=True)
        previous_rank_level = int(balance_row.rank_level)
        new_balance = int(balance_row.balance) + int(amount)
        if new_balance < 0:
            required_amount = abs(amount)
            missing_amount = max(0, required_amount - int(balance_row.balance))
            raise AppError(
                code="insufficient_funds",
                message="You need a few more Lumens to complete this action.",
                status_code=400,
                details={
                    "balance": int(balance_row.balance),
                    "required": required_amount,
                    "missing": missing_amount,
                },
                message_key="errors.insufficient_funds",
                message_params={
                    "missing": missing_amount,
                    "required": required_amount,
                },
            )

        if amount != 0:
            balance_row.balance = new_balance
            if amount > 0:
                balance_row.total_earned += amount
            else:
                balance_row.total_spent += abs(amount)

        rank_points, rank_level = self._recompute_rank(balance_row)
        rank_up = rank_level > previous_rank_level

        await self._session.flush()
        if amount != 0:
            await self._session.execute(
                update(User).where(User.id == user_id).values(mission_credits=new_balance)
            )

        merged_meta = dict(metadata or {})
        merged_meta.setdefault("rank_points", rank_points)
        merged_meta.setdefault("rank_level", rank_level)
        merged_meta.setdefault("rank_next_threshold", self.rank_next_threshold(rank_level))
        if rank_up:
            merged_meta["rank_up"] = True
            merged_meta["rank_level_from"] = previous_rank_level
            merged_meta["rank_level_to"] = rank_level

        txn = CurrencyTransaction(
            user_id=user_id,
            amount=amount,
            balance_after=new_balance,
            reason=reason,
            context=context,
            source_id=source_id,
            meta=merged_meta,
            created_at=now,
        )
        self._session.add(txn)
        await self._session.flush()
        await self._session.refresh(txn)
        return txn

    async def list_recent_transactions(self, user_id: uuid.UUID, limit: int = 20) -> list[CurrencyTransaction]:
        stmt = (
            select(CurrencyTransaction)
            .where(CurrencyTransaction.user_id == user_id)
            .order_by(CurrencyTransaction.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def has_transaction(self, *, user_id: uuid.UUID, reason: CurrencyTransactionType, context: str) -> bool:
        stmt = (
            select(CurrencyTransaction.id)
            .where(
                CurrencyTransaction.user_id == user_id,
                CurrencyTransaction.reason == reason,
                CurrencyTransaction.context == context,
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def summary(self, user_id: uuid.UUID) -> tuple[int, int, int]:
        row = await self.ensure_balance_row(user_id)
        return int(row.balance), int(row.total_earned), int(row.total_spent)

    async def get_rank_snapshot(self, user_id: uuid.UUID) -> tuple[int, int, int]:
        row = await self.ensure_balance_row(user_id)
        return int(row.rank_points), int(row.rank_level), int(self.rank_next_threshold(int(row.rank_level)))

    async def get_premium_unlock_until(self, user_id: uuid.UUID) -> datetime | None:
        row = await self._session.execute(select(User.premium_unlock_until).where(User.id == user_id))
        return row.scalar_one_or_none()

    async def apply_purchase_streak(self, user_id: uuid.UUID, *, now: datetime | None = None) -> tuple[int, float]:
        now = now or datetime.now(timezone.utc)
        row = await self.ensure_balance_row(user_id, for_update=True)

        previous = row.last_spend_at
        today = now.date()
        if previous is None:
            row.spend_streak_days = 1
        else:
            previous_dt = previous if previous.tzinfo is not None else previous.replace(tzinfo=timezone.utc)
            previous_day = previous_dt.astimezone(timezone.utc).date()
            if previous_day == today:
                row.spend_streak_days = max(1, int(row.spend_streak_days))
            elif previous_day == today - timedelta(days=1):
                row.spend_streak_days = max(1, int(row.spend_streak_days)) + 1
            else:
                row.spend_streak_days = 1

        row.last_spend_at = now
        await self._session.flush()
        return int(row.spend_streak_days), self.spend_streak_multiplier(int(row.spend_streak_days))

    async def record_daily_check_in(
        self,
        user_id: uuid.UUID,
        *,
        now: datetime | None = None,
    ) -> tuple[UserCurrencyBalance, bool]:
        now = now or datetime.now(timezone.utc)
        row = await self.ensure_balance_row(user_id, for_update=True)
        today = now.date()

        previous = row.last_check_in_at
        if previous is not None:
            previous_dt = previous if previous.tzinfo is not None else previous.replace(tzinfo=timezone.utc)
            previous_day = previous_dt.astimezone(timezone.utc).date()
            if previous_day == today:
                return row, False
            if previous_day == today - timedelta(days=1):
                row.current_streak = max(1, int(row.current_streak)) + 1
            elif int(row.streak_freeze_tokens) > 0:
                # Preserve momentum once by consuming a freeze token.
                row.streak_freeze_tokens = max(0, int(row.streak_freeze_tokens) - 1)
                row.current_streak = max(1, int(row.current_streak)) + 1
            else:
                row.current_streak = 1
        else:
            row.current_streak = 1

        row.best_streak = max(int(row.best_streak), int(row.current_streak))
        row.last_check_in_at = now
        await self._session.flush()
        await self._session.refresh(row)
        return row, True

    async def add_streak_freeze_tokens(self, user_id: uuid.UUID, amount: int = 1) -> int:
        if amount <= 0:
            return 0
        row = await self.ensure_balance_row(user_id, for_update=True)
        row.streak_freeze_tokens = int(row.streak_freeze_tokens) + amount
        await self._session.flush()
        return int(row.streak_freeze_tokens)

    async def list_pending_locked_rewards(self, user_id: uuid.UUID) -> list[UserLockedReward]:
        now = datetime.now(timezone.utc)
        await self.expire_locked_rewards(user_id=user_id, now=now)
        stmt = (
            select(UserLockedReward)
            .where(
                UserLockedReward.user_id == user_id,
                UserLockedReward.status == LockedRewardStatus.pending,
            )
            .order_by(UserLockedReward.created_at.asc())
        )
        rows = await self._session.execute(stmt)
        return list(rows.scalars().all())

    async def create_locked_cashback(
        self,
        *,
        user_id: uuid.UUID,
        amount: int,
        source_purchase_id: uuid.UUID | None,
        unlock_by: datetime,
        metadata: dict[str, Any] | None = None,
    ) -> UserLockedReward | None:
        if amount <= 0:
            return None
        reward = UserLockedReward(
            user_id=user_id,
            source_purchase_id=source_purchase_id,
            amount=amount,
            required_mission_count=LOCKED_CASHBACK_REQUIRED_MISSIONS,
            completed_mission_count=0,
            status=LockedRewardStatus.pending,
            unlock_by=unlock_by,
            meta=metadata,
        )
        self._session.add(reward)
        await self._session.flush()
        await self._session.refresh(reward)
        return reward

    async def expire_locked_rewards(self, *, user_id: uuid.UUID, now: datetime | None = None) -> int:
        now = now or datetime.now(timezone.utc)
        stmt = (
            update(UserLockedReward)
            .where(
                UserLockedReward.user_id == user_id,
                UserLockedReward.status == LockedRewardStatus.pending,
                UserLockedReward.unlock_by.is_not(None),
                UserLockedReward.unlock_by < now,
            )
            .values(status=LockedRewardStatus.expired, expired_at=now)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return int(getattr(result, "rowcount", 0) or 0)

    async def progress_locked_cashback(
        self,
        *,
        user_id: uuid.UUID,
        mission_progress: int = 1,
        now: datetime | None = None,
    ) -> list[UserLockedReward]:
        now = now or datetime.now(timezone.utc)
        if mission_progress <= 0:
            return []

        await self.expire_locked_rewards(user_id=user_id, now=now)

        stmt = (
            select(UserLockedReward)
            .where(
                UserLockedReward.user_id == user_id,
                UserLockedReward.status == LockedRewardStatus.pending,
                (UserLockedReward.unlock_by.is_(None) | (UserLockedReward.unlock_by >= now)),
            )
            .order_by(UserLockedReward.created_at.asc())
        )
        if not self._is_sqlite():
            stmt = stmt.with_for_update()

        rows = (await self._session.execute(stmt)).scalars().all()

        unlocked: list[UserLockedReward] = []
        for row in rows:
            row.completed_mission_count = int(row.completed_mission_count) + mission_progress
            if int(row.completed_mission_count) >= int(row.required_mission_count):
                row.status = LockedRewardStatus.unlocked
                row.unlocked_at = now
                unlocked.append(row)

        await self._session.flush()

        for row in unlocked:
            await self.adjust_balance(
                user_id=user_id,
                amount=int(row.amount),
                reason=CurrencyTransactionType.cashback_unlocked,
                context=f"cashback_unlock:{row.id}",
                source_id=row.id,
                metadata={
                    "locked_reward_id": str(row.id),
                    "source_purchase_id": str(row.source_purchase_id) if row.source_purchase_id else None,
                    "required_mission_count": int(row.required_mission_count),
                },
                now=now,
            )

        return unlocked

    async def grant_active_boost(
        self,
        *,
        user_id: uuid.UUID,
        source_purchase_id: uuid.UUID | None,
        boost_percent: int,
        missions_total: int,
        expires_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> UserActiveBoost | None:
        if boost_percent <= 0 or missions_total <= 0:
            return None
        boost = UserActiveBoost(
            user_id=user_id,
            source_purchase_id=source_purchase_id,
            boost_percent=boost_percent,
            missions_total=missions_total,
            missions_used=0,
            status=BoostStatus.active,
            expires_at=expires_at,
            meta=metadata,
        )
        self._session.add(boost)
        await self._session.flush()
        await self._session.refresh(boost)
        return boost

    async def _expire_old_boosts(self, user_id: uuid.UUID, *, now: datetime) -> None:
        await self._session.execute(
            update(UserActiveBoost)
            .where(
                UserActiveBoost.user_id == user_id,
                UserActiveBoost.status == BoostStatus.active,
                UserActiveBoost.expires_at.is_not(None),
                UserActiveBoost.expires_at < now,
            )
            .values(status=BoostStatus.expired)
        )

    async def list_active_boosts(self, *, user_id: uuid.UUID, now: datetime | None = None) -> list[UserActiveBoost]:
        now = now or datetime.now(timezone.utc)
        await self._expire_old_boosts(user_id, now=now)
        rows = await self._session.execute(
            select(UserActiveBoost)
            .where(
                UserActiveBoost.user_id == user_id,
                UserActiveBoost.status == BoostStatus.active,
            )
            .order_by(UserActiveBoost.created_at.asc())
        )
        return list(rows.scalars().all())

    async def consume_active_boost(
        self,
        *,
        user_id: uuid.UUID,
        now: datetime | None = None,
    ) -> tuple[float, int | None, int | None]:
        now = now or datetime.now(timezone.utc)
        await self._expire_old_boosts(user_id, now=now)

        row = (
            await self._session.execute(
                select(UserActiveBoost)
                .where(
                    UserActiveBoost.user_id == user_id,
                    UserActiveBoost.status == BoostStatus.active,
                )
                .order_by(UserActiveBoost.created_at.asc())
                .limit(1)
            )
        ).scalar_one_or_none()

        if row is None:
            return 1.0, None, None

        row.missions_used = int(row.missions_used) + 1
        if int(row.missions_used) >= int(row.missions_total):
            row.status = BoostStatus.exhausted
        await self._session.flush()

        missions_left = max(0, int(row.missions_total) - int(row.missions_used))
        return 1.0 + (int(row.boost_percent) / 100.0), int(row.boost_percent), missions_left

    def _item_synergy_categories(self, item_meta: dict | None, purchase_meta: dict | None) -> set[str]:
        out: set[str] = set()
        for payload in (purchase_meta or {}, item_meta or {}):
            raw = payload.get("synergy_categories")
            if isinstance(raw, list):
                out.update(str(value).strip().lower() for value in raw if value)
            raw_single = payload.get("synergy_category")
            if isinstance(raw_single, str) and raw_single.strip():
                out.add(raw_single.strip().lower())
        return out

    async def owned_synergy_bonus(self, *, user_id: uuid.UUID, mission_category: str | None) -> int:
        category = (mission_category or "").strip().lower()
        if not category:
            return 0

        rows = await self._session.execute(
            select(UserPurchase.meta, StoreItem.meta)
            .join(StoreItem, StoreItem.id == UserPurchase.store_item_id)
            .where(
                UserPurchase.user_id == user_id,
                UserPurchase.status == PurchaseStatus.completed,
            )
            .order_by(UserPurchase.created_at.desc())
            .limit(120)
        )

        best_tier = 0
        for purchase_meta, item_meta in rows.all():
            categories = self._item_synergy_categories(item_meta, purchase_meta)
            if category not in categories:
                continue
            tier_raw = None
            for payload in (purchase_meta or {}, item_meta or {}):
                if payload.get("upgrade_tier") is not None:
                    tier_raw = payload.get("upgrade_tier")
                    break
            try:
                tier = int(tier_raw or 1)
            except (TypeError, ValueError):
                tier = 1
            best_tier = max(best_tier, tier)

        if best_tier <= 0:
            return 0
        return 2 if best_tier >= 2 else 1

    async def sum_mission_earnings_today(
        self,
        *,
        user_id: uuid.UUID,
        start_of_day: datetime,
        end_of_day: datetime,
    ) -> int:
        reasons = (
            CurrencyTransactionType.mission_reward,
            CurrencyTransactionType.surprise_reward,
            CurrencyTransactionType.spend_streak_bonus,
            CurrencyTransactionType.rank_bonus,
        )
        value = (
            await self._session.execute(
                select(func.coalesce(func.sum(CurrencyTransaction.amount), 0))
                .where(
                    CurrencyTransaction.user_id == user_id,
                    CurrencyTransaction.reason.in_(reasons),
                    CurrencyTransaction.created_at >= start_of_day,
                    CurrencyTransaction.created_at < end_of_day,
                )
            )
        ).scalar_one()
        return int(value or 0)

    async def count_mission_events_since(
        self,
        *,
        user_id: uuid.UUID,
        mission_id: uuid.UUID,
        since: datetime,
        event_type: str | None = None,
    ) -> int:
        where = [
            MissionCompletionEvent.user_id == user_id,
            MissionCompletionEvent.mission_id == mission_id,
            MissionCompletionEvent.created_at >= since,
        ]
        if event_type is not None:
            where.append(MissionCompletionEvent.event_type == event_type)

        value = (
            await self._session.execute(
                select(func.count())
                .select_from(MissionCompletionEvent)
                .where(*where)
            )
        ).scalar_one()
        return int(value or 0)

    async def has_recent_mission_event(
        self,
        *,
        user_id: uuid.UUID,
        mission_id: uuid.UUID,
        event_type: str,
        since: datetime,
    ) -> bool:
        row = (
            await self._session.execute(
                select(MissionCompletionEvent.id)
                .where(
                    MissionCompletionEvent.user_id == user_id,
                    MissionCompletionEvent.mission_id == mission_id,
                    MissionCompletionEvent.event_type == event_type,
                    MissionCompletionEvent.created_at >= since,
                )
                .limit(1)
            )
        ).scalar_one_or_none()
        return row is not None

    async def classify_user_segment(self, *, user_id: uuid.UUID, now: datetime | None = None) -> str:
        now = now or datetime.now(timezone.utc)
        row = await self.ensure_balance_row(user_id)
        balance = int(row.balance)

        mission_recent = (
            await self._session.execute(
                select(func.count())
                .select_from(MissionCompletionEvent)
                .where(
                    MissionCompletionEvent.user_id == user_id,
                    MissionCompletionEvent.created_at >= now - timedelta(hours=SEGMENT_MISSION_LOOKBACK_HOURS),
                )
            )
        ).scalar_one()
        mission_recent_count = int(mission_recent or 0)

        spend_recent = (
            await self._session.execute(
                select(func.count())
                .select_from(CurrencyTransaction)
                .where(
                    CurrencyTransaction.user_id == user_id,
                    CurrencyTransaction.amount < 0,
                    CurrencyTransaction.reason.in_(
                        (
                            CurrencyTransactionType.store_purchase,
                            CurrencyTransactionType.boost_purchase,
                            CurrencyTransactionType.upgrade_purchase,
                            CurrencyTransactionType.marketplace_purchase,
                        )
                    ),
                    CurrencyTransaction.created_at >= now - timedelta(days=SEGMENT_SPEND_LOOKBACK_DAYS),
                )
            )
        ).scalar_one()
        spend_recent_count = int(spend_recent or 0)

        if mission_recent_count <= 0:
            return "inactive"
        if balance >= HOARDER_BALANCE_THRESHOLD and spend_recent_count <= HOARDER_SPEND_RECENT_MAX:
            return "hoarder"
        if spend_recent_count >= SPENDER_SPEND_RECENT_MIN:
            return "spender"
        return "balanced"

    async def resolve_catchup_boost(
        self,
        *,
        user_id: uuid.UUID,
        segment: str,
        now: datetime | None = None,
    ) -> tuple[float, int, bool]:
        now = now or datetime.now(timezone.utc)
        row = await self.ensure_balance_row(user_id, for_update=True)

        expires_at = row.catchup_boost_expires_at
        expires_dt = (
            expires_at if expires_at is not None and expires_at.tzinfo is not None
            else expires_at.replace(tzinfo=timezone.utc) if expires_at is not None
            else None
        )
        pct = max(0, int(row.catchup_boost_pct))

        if segment == "inactive":
            if expires_dt is None or expires_dt < now or pct <= 0:
                row.catchup_boost_pct = CATCHUP_BOOST_PCT
                row.catchup_boost_expires_at = now + timedelta(hours=CATCHUP_BOOST_EXPIRY_HOURS)
                await self._session.flush()
                return 1.0 + (CATCHUP_BOOST_PCT / 100.0), CATCHUP_BOOST_PCT, True

        if expires_dt is not None and expires_dt >= now and pct > 0:
            return 1.0 + (pct / 100.0), pct, False

        if expires_dt is not None and expires_dt < now and pct > 0:
            row.catchup_boost_pct = 0
            row.catchup_boost_expires_at = None
            await self._session.flush()

        return 1.0, 0, False

    async def should_offer_streak_recovery(
        self,
        *,
        user_id: uuid.UUID,
        now: datetime | None = None,
    ) -> bool:
        now = now or datetime.now(timezone.utc)
        row = await self.ensure_balance_row(user_id)
        if int(row.current_streak) < 3:
            return False
        if row.last_check_in_at is None:
            return False
        previous_dt = (
            row.last_check_in_at
            if row.last_check_in_at.tzinfo is not None
            else row.last_check_in_at.replace(tzinfo=timezone.utc)
        )
        previous_day = previous_dt.astimezone(timezone.utc).date()
        today = now.date()
        return previous_day == (today - timedelta(days=1))

    async def track_second_purchase_challenge(self, *, user_id: uuid.UUID, now: datetime | None = None) -> str | None:
        now = now or datetime.now(timezone.utc)
        row = await self.ensure_balance_row(user_id, for_update=True)

        if row.second_purchase_challenge_started_at is None:
            row.second_purchase_challenge_started_at = now
            row.second_purchase_challenge_expires_at = now + timedelta(hours=SECOND_PURCHASE_CHALLENGE_WINDOW_HOURS)
            row.second_purchase_challenge_completed_at = None
            await self._session.flush()
            return "started"

        if row.second_purchase_challenge_completed_at is not None:
            return None

        expires_at = row.second_purchase_challenge_expires_at
        if expires_at is not None:
            expires_dt = expires_at if expires_at.tzinfo is not None else expires_at.replace(tzinfo=timezone.utc)
            if now > expires_dt:
                return "expired"

        started_at = row.second_purchase_challenge_started_at
        if started_at is None:
            return None

        started_dt = started_at if started_at.tzinfo is not None else started_at.replace(tzinfo=timezone.utc)
        purchase_count = (
            await self._session.execute(
                select(func.count())
                .select_from(UserPurchase)
                .where(
                    UserPurchase.user_id == user_id,
                    UserPurchase.status == PurchaseStatus.completed,
                    UserPurchase.created_at >= started_dt,
                )
            )
        ).scalar_one()

        if int(purchase_count or 0) >= 2:
            row.second_purchase_challenge_completed_at = now
            await self._session.flush()
            return "completed"
        return "in_progress"

    async def grant_reward_credits(
        self,
        *,
        user_id: uuid.UUID,
        mission_id: uuid.UUID,
        mission_slug: str,
        credits: int,
        now: datetime | None = None,
    ) -> None:
        if credits <= 0:
            return
        await self.adjust_balance(
            user_id=user_id,
            amount=credits,
            reason=CurrencyTransactionType.mission_reward,
            context=f"mission:{mission_slug}",
            source_id=mission_id,
            metadata={"type": MissionRewardType.credits.value, "mission_id": str(mission_id)},
            now=now,
        )
