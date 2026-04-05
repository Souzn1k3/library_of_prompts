import secrets
from typing import Any

from app.infrastructure.db.models import StoreItem, StoreItemKind
from app.modules.economy.config.tuning import (
    DEFAULT_BOOST_MISSIONS,
    DEFAULT_BOOST_PCT,
    DEFAULT_PREMIUM_DAYS,
    LOCKED_CASHBACK_REQUIRED_MISSIONS,
    LOCKED_CASHBACK_UNLOCK_WINDOW_HOURS,
    SECOND_PURCHASE_CHALLENGE_BOOST_MISSIONS,
    SECOND_PURCHASE_CHALLENGE_BOOST_PCT,
)
from app.modules.economy.model.store import StoreRewardRead


class StoreRewardService:
    def first_purchase_reward(self, amount: int) -> StoreRewardRead:
        return StoreRewardRead(
            kind="bonus_lumens",
            title="First purchase bonus",
            description="You spent Lumens once, so we topped up your wallet for the next unlock.",
            amount=amount,
            metadata={"reward_type": "first_purchase"},
        )

    def locked_cashback_reward(self, amount: int) -> StoreRewardRead:
        return StoreRewardRead(
            kind="locked_cashback",
            title="Locked cashback added",
            description=(
                f"Complete {LOCKED_CASHBACK_REQUIRED_MISSIONS} missions in "
                f"{LOCKED_CASHBACK_UNLOCK_WINDOW_HOURS} hours to unlock this cashback."
            ),
            amount=amount,
            metadata={
                "reward_type": "locked_cashback",
                "unlock_rule": f"{LOCKED_CASHBACK_REQUIRED_MISSIONS}_missions_{LOCKED_CASHBACK_UNLOCK_WINDOW_HOURS}h",
            },
        )

    def second_purchase_challenge_reward(self, amount: int) -> StoreRewardRead:
        return StoreRewardRead(
            kind="second_purchase_challenge",
            title="Second purchase challenge completed",
            description="Bonus Lumens and a short mission booster are now active.",
            amount=amount,
            metadata={
                "reward_type": "second_purchase",
                "boost_pct": SECOND_PURCHASE_CHALLENGE_BOOST_PCT,
                "boost_missions": SECOND_PURCHASE_CHALLENGE_BOOST_MISSIONS,
            },
        )

    def reward_from_purchase_meta(self, meta: dict[str, Any] | None) -> StoreRewardRead | None:
        if not meta:
            return None
        amount = meta.get("first_purchase_bonus_amount")
        if isinstance(amount, int) and amount > 0:
            return self.first_purchase_reward(amount)
        return None

    def apply_item_reward_metadata(self, *, item: StoreItem, purchase_metadata: dict[str, Any]) -> None:
        meta = item.meta or {}
        purchase_metadata["item_kind"] = item.kind.value
        purchase_metadata["upgrade_track"] = meta.get("upgrade_track")
        purchase_metadata["upgrade_tier"] = meta.get("upgrade_tier")

        if item.kind == StoreItemKind.starter:
            starter_type = str(meta.get("starter_type", "starter"))
            purchase_metadata["starter_type"] = starter_type
            purchase_metadata["reward_title"] = meta.get("reward_title") or item.title
            purchase_metadata["reward_body"] = meta.get("reward_body")
            if starter_type == "discount":
                percent = int(meta.get("discount_percent", 10))
                code = f"{meta.get('code_prefix', 'START')}-{secrets.token_hex(3).upper()}"
                purchase_metadata["discount_percent"] = percent
                purchase_metadata["discount_code"] = code
            return

        if item.kind == StoreItemKind.premium_pass:
            purchase_metadata["premium_days"] = int(meta.get("premium_days", DEFAULT_PREMIUM_DAYS))
            return

        if item.kind == StoreItemKind.subscription_discount:
            percent = int(meta.get("discount_percent", 20))
            code = f"{meta.get('code_prefix', 'LMN')}-{secrets.token_hex(3).upper()}"
            purchase_metadata["discount_percent"] = percent
            purchase_metadata["discount_code"] = code
            return

        if item.kind == StoreItemKind.premium_prompt_unlock:
            purchase_metadata["prompt_id"] = meta.get("prompt_id")
            purchase_metadata["prompt_slug"] = meta.get("prompt_slug")
            purchase_metadata["prompt_title"] = meta.get("prompt_title")
            return

        if item.kind == StoreItemKind.prompt_bundle:
            purchase_metadata["prompt_ids"] = list(meta.get("prompt_ids", []))
            purchase_metadata["prompt_slugs"] = list(meta.get("prompt_slugs", []))
            purchase_metadata["prompt_titles"] = list(meta.get("prompt_titles", []))
            purchase_metadata["bundle_size"] = len(purchase_metadata["prompt_ids"])
            return

        if item.kind == StoreItemKind.boost:
            purchase_metadata["boost_pct"] = int(meta.get("boost_pct", DEFAULT_BOOST_PCT))
            purchase_metadata["boost_missions"] = int(meta.get("boost_missions", DEFAULT_BOOST_MISSIONS))
