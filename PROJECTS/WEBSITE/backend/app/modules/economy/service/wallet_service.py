import uuid
from datetime import datetime, timezone, timedelta

from app.core.errors import AppError
from app.infrastructure.db.models import CurrencyTransactionType, StoreItemKind, User
from app.modules.economy.model.wallet import (
    CurrencyTransactionRead,
    WalletBenefitRead,
    WalletPurchaseRead,
    WalletRead,
)
from app.modules.economy.repository.store_repository import StoreRepository
from app.modules.economy.repository.wallet_repository import WalletRepository


class WalletService:
    def __init__(self, repo: WalletRepository, store_repo: StoreRepository | None = None) -> None:
        self._repo = repo
        self._store_repo = store_repo

    async def ensure_wallet(self, user_id: uuid.UUID) -> None:
        await self._repo.ensure_balance_row(user_id)

    def _can_check_in(self, last_check_in_at: datetime | None) -> bool:
        if last_check_in_at is None:
            return True
        current = last_check_in_at if last_check_in_at.tzinfo is not None else last_check_in_at.replace(tzinfo=timezone.utc)
        return current.astimezone(timezone.utc).date() < datetime.now(timezone.utc).date()

    async def _active_benefits(self, user: User, *, premium_unlock_until: datetime | None = None) -> list[WalletBenefitRead]:
        benefits: list[WalletBenefitRead] = []

        effective_unlock_until = premium_unlock_until if premium_unlock_until is not None else user.premium_unlock_until
        if effective_unlock_until is not None:
            unlock_until = (
                effective_unlock_until
                if effective_unlock_until.tzinfo is not None
                else effective_unlock_until.replace(tzinfo=timezone.utc)
            )
            if unlock_until > datetime.now(timezone.utc):
                benefits.append(
                    WalletBenefitRead(
                        key="premium_access",
                        kind="premium_access",
                        metadata={"source": "wallet_unlock"},
                        expires_at=unlock_until,
                    )
                )

        if self._store_repo is None:
            return benefits

        recent_purchases = await self._store_repo.list_recent_purchases(user.id, limit=10)
        seen_codes: set[str] = set()
        seen_unlocks: set[str] = set()
        for purchase in recent_purchases:
            item = purchase.item
            if item is None or purchase.meta is None:
                continue
            discount_code = purchase.meta.get("discount_code")
            if item.kind.value == "subscription_discount" and isinstance(discount_code, str) and discount_code not in seen_codes:
                seen_codes.add(discount_code)
                benefits.append(
                    WalletBenefitRead(
                        key=f"discount_code:{discount_code}",
                        kind="subscription_discount",
                        metadata={
                            "code": discount_code,
                            "discount_percent": purchase.meta.get("discount_percent"),
                            "item_slug": item.slug,
                        },
                        expires_at=None,
                    )
                )
            if item.kind.value in {"premium_prompt_unlock", "prompt_bundle"}:
                unlock_key = item.slug
                if unlock_key in seen_unlocks:
                    continue
                seen_unlocks.add(unlock_key)
                benefits.append(
                    WalletBenefitRead(
                        key=f"prompt_unlock:{unlock_key}",
                        kind=item.kind.value,
                        metadata={
                            "item_slug": item.slug,
                            "item_title": item.title,
                            "prompt_title": purchase.meta.get("prompt_title"),
                            "prompt_titles": purchase.meta.get("prompt_titles"),
                        },
                        expires_at=None,
                    )
                )
        return benefits

    async def get_wallet(self, user: User, *, limit: int = 20) -> WalletRead:
        balance_row = await self._repo.get_balance_row(user.id)
        premium_unlock_until = await self._repo.get_premium_unlock_until(user.id)
        recent = await self._repo.list_recent_transactions(user.id, limit=limit)
        recent_purchases = (
            await self._store_repo.list_recent_purchases(user.id, limit=8)
            if self._store_repo is not None
            else []
        )
        return WalletRead(
            balance=int(balance_row.balance),
            currency="LMN",
            currency_name="Lumens",
            currency_symbol="LMN",
            total_earned=int(balance_row.total_earned),
            total_spent=int(balance_row.total_spent),
            current_streak=int(balance_row.current_streak),
            best_streak=int(balance_row.best_streak),
            last_check_in_at=balance_row.last_check_in_at,
            check_in_available=self._can_check_in(balance_row.last_check_in_at),
            premium_unlock_until=premium_unlock_until,
            active_benefits=await self._active_benefits(user, premium_unlock_until=premium_unlock_until),
            recent_purchases=[
                WalletPurchaseRead(
                    id=row.id,
                    item_slug=row.item.slug if row.item is not None else "",
                    item_title=row.item.title if row.item is not None else "",
                    kind=row.item.kind if row.item is not None else StoreItemKind.future,
                    price_paid=row.price_paid,
                    status=row.status,
                    metadata=row.meta,
                    created_at=row.created_at,
                )
                for row in recent_purchases
                if row.item is not None
            ],
            recent=[
                CurrencyTransactionRead(
                    id=row.id,
                    amount=row.amount,
                    balance_after=row.balance_after,
                    reason=row.reason,
                    context=row.context,
                    metadata=row.meta,
                    created_at=row.created_at,
                )
                for row in recent
            ],
        )

    async def adjust(
        self,
        *,
        user_id: uuid.UUID,
        amount: int,
        reason: CurrencyTransactionType,
        context: str | None = None,
        source_id: uuid.UUID | None = None,
        metadata: dict | None = None,
        now: datetime | None = None,
    ) -> None:
        await self._repo.adjust_balance(
            user_id=user_id,
            amount=amount,
            reason=reason,
            context=context,
            source_id=source_id,
            metadata=metadata,
            now=now,
        )

    async def reward_mission(self, *, user_id: uuid.UUID, mission_id: uuid.UUID, mission_slug: str, credits: int) -> None:
        await self._repo.grant_reward_credits(
            user_id=user_id,
            mission_id=mission_id,
            mission_slug=mission_slug,
            credits=credits,
        )

    async def grant_premium_days(self, user: User, days: int) -> datetime:
        now = datetime.now(timezone.utc)
        desired = now + timedelta(days=days)
        current = user.premium_unlock_until
        if current is not None and current > desired:
            desired = current
        user.premium_unlock_until = desired
        return desired

    async def apply_streak_bonus(self, user_id: uuid.UUID, amount: int, *, today: datetime | None = None) -> None:
        today = today or datetime.now(timezone.utc)
        await self.adjust(
            user_id=user_id,
            amount=amount,
            reason=CurrencyTransactionType.streak_bonus,
            context=f"streak:{today.date().isoformat()}",
            metadata={"streak_bonus": True},
            now=today,
        )

    async def daily_checkin_bonus(self, user_id: uuid.UUID, *, amount: int = 2) -> None:
        now = datetime.now(timezone.utc)
        balance_row, applied = await self._repo.record_daily_check_in(user_id, now=now)
        if not applied:
            return

        milestone_bonus = 0
        if balance_row.current_streak >= 14:
            milestone_bonus = 10
        elif balance_row.current_streak >= 7:
            milestone_bonus = 5
        elif balance_row.current_streak >= 3:
            milestone_bonus = 2

        total_amount = amount + milestone_bonus
        await self.adjust(
            user_id=user_id,
            amount=total_amount,
            reason=CurrencyTransactionType.streak_bonus,
            context=f"checkin:{now.date().isoformat()}",
            metadata={
                "daily_checkin": True,
                "base_amount": amount,
                "milestone_bonus": milestone_bonus,
                "current_streak": balance_row.current_streak,
            },
            now=now,
        )
