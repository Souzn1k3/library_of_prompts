from __future__ import annotations

from datetime import datetime, timezone

from app.infrastructure.db.models import User
from app.modules.economy.model.wallet import WalletBenefitRead
from app.modules.economy.repository.store_repository import StoreRepository
from app.modules.economy.repository.wallet_repository import WalletRepository


class WalletBenefitResolver:
    def __init__(self, repo: WalletRepository, store_repo: StoreRepository | None = None) -> None:
        self._repo = repo
        self._store_repo = store_repo

    async def active_benefits(self, user: User, *, premium_unlock_until: datetime | None = None) -> list[WalletBenefitRead]:
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
        seen_starters: set[str] = set()
        for purchase in recent_purchases:
            item = purchase.item
            if item is None or purchase.meta is None:
                continue
            discount_code = purchase.meta.get("discount_code")
            if item.kind.value in {"starter", "subscription_discount"} and isinstance(discount_code, str) and discount_code not in seen_codes:
                seen_codes.add(discount_code)
                benefits.append(
                    WalletBenefitRead(
                        key=f"discount_code:{discount_code}",
                        kind=item.kind.value,
                        metadata={
                            "code": discount_code,
                            "discount_percent": purchase.meta.get("discount_percent"),
                            "item_slug": item.slug,
                            "item_title": item.title,
                        },
                        expires_at=None,
                    )
                )
            if item.kind.value == "starter" and not isinstance(discount_code, str):
                starter_key = item.slug
                if starter_key in seen_starters:
                    continue
                seen_starters.add(starter_key)
                benefits.append(
                    WalletBenefitRead(
                        key=f"starter:{starter_key}",
                        kind="starter",
                        metadata={
                            "item_slug": item.slug,
                            "item_title": item.title,
                            "reward_title": purchase.meta.get("reward_title"),
                            "reward_body": purchase.meta.get("reward_body"),
                            "starter_type": purchase.meta.get("starter_type"),
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

        active_boosts = await self._repo.list_active_boosts(user_id=user.id)
        for boost in active_boosts:
            boost_meta = boost.meta if isinstance(boost.meta, dict) else {}
            missions_total = max(0, int(boost.missions_total))
            missions_used = max(0, int(boost.missions_used))
            missions_left = max(0, missions_total - missions_used)
            benefits.append(
                WalletBenefitRead(
                    key=f"boost:{boost.id}",
                    kind="boost",
                    metadata={
                        **boost_meta,
                        "boost_pct": int(boost.boost_percent),
                        "boost_missions_total": missions_total,
                        "boost_missions_left": missions_left,
                    },
                    expires_at=boost.expires_at,
                )
            )
        return benefits
