import uuid
from typing import Any

from app.core.client_tokens import candidate_scoped_tokens, scoped_client_token, scoped_or_random_token
from app.core.errors import AppError
from app.infrastructure.db.models import StoreItem, User
from app.modules.economy.model.store import PurchaseResult


class StorePurchaseHelpersMixin:
    def _scoped_client_token(self, user_id: uuid.UUID, raw_token: str, *, prefix: str = "store") -> str:
        return scoped_client_token(user_id, raw_token, prefix=prefix)

    def _effective_client_token(self, *, user_id: uuid.UUID, item: StoreItem, client_token: str | None) -> str:
        raw = (client_token or "").strip()
        if self._catalog.is_one_time_item(item):
            return self._scoped_client_token(user_id, f"one-time:{item.id}")
        if raw:
            return self._scoped_client_token(user_id, raw)
        return scoped_or_random_token(user_id, None, prefix="store")

    async def _find_purchase_by_client_token(self, *, user_id: uuid.UUID, client_token: str) -> Any | None:
        candidates = candidate_scoped_tokens(user_id, client_token, prefix="store")
        seen: set[str] = set()
        for token in candidates:
            if token in seen:
                continue
            seen.add(token)
            existing = await self._store.get_purchase_by_client_token(user_id=user_id, client_token=token)
            if existing is not None:
                return existing
        return None

    async def _purchase_result_from_existing(self, *, user: User, existing: Any) -> PurchaseResult:
        feedback = await self._catalog.build_action_feedback(user)
        if feedback.wallet is None:
            raise AppError(
                code="wallet_missing",
                message="Wallet could not be loaded.",
                status_code=500,
                message_key="errors.wallet_missing",
            )
        wallet = feedback.wallet
        return PurchaseResult(
            purchase=await self._catalog.serialize_purchase(existing, balance=wallet.balance),
            wallet=wallet,
            available_items=feedback.available_items,
            newly_affordable_items=feedback.newly_affordable_items,
            best_item=feedback.best_item,
            first_purchase_reward=self._rewards.reward_from_purchase_meta(existing.meta),
            locked_cashback_reward=None,
            second_purchase_challenge_reward=None,
        )

    async def _validate_upgrade_path(self, *, user: User, item: StoreItem) -> None:
        meta = item.meta or {}
        track = str(meta.get("upgrade_track") or "").strip().lower()
        tier_raw = meta.get("upgrade_tier")
        try:
            tier = int(tier_raw or 1)
        except (TypeError, ValueError):
            tier = 1
        if tier <= 1 or not track:
            return

        purchases = await self._store.list_all_completed_purchases(user.id)
        required_tier = tier - 1
        for purchase in purchases:
            payload = purchase.meta or {}
            payload_track = str(payload.get("upgrade_track") or "").strip().lower()
            if payload_track != track:
                continue
            try:
                payload_tier = int(payload.get("upgrade_tier") or 1)
            except (TypeError, ValueError):
                payload_tier = 1
            if payload_tier >= required_tier:
                return

        raise AppError(
            code="store_upgrade_locked",
            message="Upgrade tier is locked until previous tier is owned.",
            status_code=409,
            details={"upgrade_track": track, "required_tier": required_tier},
            message_key="errors.store_upgrade_locked",
        )
