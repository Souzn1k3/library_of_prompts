import secrets
from datetime import datetime, timezone
from typing import Any

from app.core.errors import AppError
from app.infrastructure.db.models import CurrencyTransactionType, StoreItem, StoreItemKind, User
from app.modules.economy.model.store import PurchaseRead, PurchaseResult, StoreItemRead
from app.modules.economy.model.wallet import WalletRead
from app.modules.economy.repository.store_repository import StoreRepository
from app.modules.economy.repository.wallet_repository import WalletRepository
from app.modules.economy.service.wallet_service import WalletService


class StoreService:
    def __init__(self, store_repo: StoreRepository, wallet_repo: WalletRepository) -> None:
        self._store = store_repo
        self._wallet_repo = wallet_repo
        self._wallet = WalletService(wallet_repo, store_repo)

    def _is_one_time_item(self, item: StoreItem) -> bool:
        return item.kind in {
            StoreItemKind.subscription_discount,
            StoreItemKind.premium_prompt_unlock,
            StoreItemKind.prompt_bundle,
        }

    async def _serialize_item(self, row: StoreItem, *, owned: bool = False) -> StoreItemRead:
        return StoreItemRead(
            id=row.id,
            slug=row.slug,
            title=row.title,
            description=row.description,
            price=row.price,
            kind=row.kind,
            availability=row.availability,
            metadata=row.meta,
            is_active=row.is_active,
            owned=owned,
        )

    async def _serialize_purchase(self, purchase, *, fallback_item: StoreItem | None = None) -> PurchaseRead:
        item = purchase.item or fallback_item
        if item is None:
            raise AppError(code="store_item_missing", message="Purchase item could not be loaded.", status_code=500)
        return PurchaseRead(
            id=purchase.id,
            status=purchase.status,
            price_paid=purchase.price_paid,
            metadata=purchase.meta,
            client_token=purchase.client_token,
            item=await self._serialize_item(item, owned=True),
            created_at=purchase.created_at,
        )

    async def list_items(self, user: User) -> list[StoreItemRead]:
        items = await self._ensure_default_items()
        purchases = await self._store.list_all_completed_purchases(user.id)
        owned_item_ids = {
            purchase.store_item_id
            for purchase in purchases
            if purchase.item is not None and self._is_one_time_item(purchase.item)
        }
        return [await self._serialize_item(item, owned=item.id in owned_item_ids) for item in items]

    async def purchase(self, *, user: User, item_slug: str, client_token: str | None = None) -> PurchaseResult:
        if client_token:
            existing = await self._store.get_purchase_by_client_token(user_id=user.id, client_token=client_token)
            if existing is not None:
                return PurchaseResult(
                    purchase=await self._serialize_purchase(existing),
                    wallet=await self._wallet.get_wallet(user, limit=20),
                )

        item = await self._store.get_item_by_slug(item_slug)
        if item is None:
            await self._ensure_default_items()
            item = await self._store.get_item_by_slug(item_slug)
        if item is None or not item.is_active:
            raise AppError(code="store_item_not_found", message="Item is not available right now.", status_code=404)
        if item.availability is not None and item.availability <= 0:
            raise AppError(code="store_item_unavailable", message="This item is sold out.", status_code=409)
        if self._is_one_time_item(item):
            owned = await self._store.get_completed_purchase_for_item(user_id=user.id, item_id=item.id)
            if owned is not None:
                raise AppError(code="store_item_owned", message="You already own this unlock.", status_code=409)

        await self._wallet_repo.ensure_balance_row(user.id)
        now = datetime.now(timezone.utc)
        txn = await self._wallet_repo.adjust_balance(
            user_id=user.id,
            amount=-item.price,
            reason=CurrencyTransactionType.store_purchase,
            context=f"store:{item.slug}:{client_token or secrets.token_hex(4)}",
            source_id=item.id,
            metadata={"title": item.title},
            now=now,
        )

        purchase_metadata: dict[str, Any] = {"transaction_id": str(txn.id)}
        if item.kind == StoreItemKind.premium_pass:
            days = int(item.meta.get("premium_days", 3) if item.meta else 3)
            premium_until = await self._wallet.grant_premium_days(user, days)
            purchase_metadata["premium_until"] = premium_until.isoformat()
            purchase_metadata["premium_days"] = days
        elif item.kind == StoreItemKind.subscription_discount:
            percent = int(item.meta.get("discount_percent", 20) if item.meta else 20)
            code = (item.meta.get("code_prefix", "LMN") if item.meta else "LMN") + "-" + secrets.token_hex(3).upper()
            purchase_metadata["discount_percent"] = percent
            purchase_metadata["discount_code"] = code
        elif item.kind == StoreItemKind.premium_prompt_unlock:
            purchase_metadata["prompt_id"] = item.meta.get("prompt_id") if item.meta else None
            purchase_metadata["prompt_slug"] = item.meta.get("prompt_slug") if item.meta else None
            purchase_metadata["prompt_title"] = item.meta.get("prompt_title") if item.meta else None
        elif item.kind == StoreItemKind.prompt_bundle:
            purchase_metadata["prompt_ids"] = list(item.meta.get("prompt_ids", []) if item.meta else [])
            purchase_metadata["prompt_slugs"] = list(item.meta.get("prompt_slugs", []) if item.meta else [])
            purchase_metadata["prompt_titles"] = list(item.meta.get("prompt_titles", []) if item.meta else [])
            purchase_metadata["bundle_size"] = len(purchase_metadata["prompt_ids"])

        if item.availability is not None:
            item.availability = max(0, item.availability - 1)

        purchase = await self._store.create_purchase(
            user_id=user.id,
            item=item,
            price_paid=item.price,
            client_token=client_token,
            meta=purchase_metadata,
        )

        wallet = await self._wallet.get_wallet(user, limit=20)
        return PurchaseResult(
            purchase=await self._serialize_purchase(purchase, fallback_item=item),
            wallet=wallet,
        )

    async def wallet(self, user: User) -> WalletRead:
        return await self._wallet.get_wallet(user, limit=25)

    async def _ensure_default_items(self) -> list[StoreItem]:
        premium_prompts = await self._store.list_featured_premium_prompts(limit=3)
        defaults: list[StoreItem] = [
            StoreItem(
                slug="pro-trial-pass",
                title="Pro Pass — 7 days",
                description="Unlock premium prompts for a full week without changing your subscription yet.",
                price=30,
                kind=StoreItemKind.premium_pass,
                meta={"premium_days": 7},
                sort_order=1,
            ),
            StoreItem(
                slug="first-month-discount",
                title="40% off first paid month",
                description="Trade Lumens for a personal discount code you can use on your next checkout.",
                price=45,
                kind=StoreItemKind.subscription_discount,
                meta={"discount_percent": 40, "code_prefix": "SAVE"},
                sort_order=2,
            ),
        ]

        for index, prompt in enumerate(premium_prompts[:2], start=3):
            defaults.append(
                StoreItem(
                    slug=f"unlock-{prompt.slug}",
                    title=f"Unlock: {prompt.title}",
                    description="Permanent access to this premium prompt from your personal library.",
                    price=18 + (index - 3) * 4,
                    kind=StoreItemKind.premium_prompt_unlock,
                    meta={
                        "prompt_id": str(prompt.id),
                        "prompt_slug": prompt.slug,
                        "prompt_title": prompt.title,
                    },
                    sort_order=index,
                )
            )

        if premium_prompts:
            defaults.append(
                StoreItem(
                    slug="prompt-power-pack",
                    title="Premium Prompt Pack",
                    description="Unlock a curated pack of premium prompts and keep them in your workflow forever.",
                    price=42,
                    kind=StoreItemKind.prompt_bundle,
                    meta={
                        "prompt_ids": [str(prompt.id) for prompt in premium_prompts],
                        "prompt_slugs": [prompt.slug for prompt in premium_prompts],
                        "prompt_titles": [prompt.title for prompt in premium_prompts],
                    },
                    sort_order=6,
                )
            )

        for item in defaults:
            existing = await self._store.get_item_by_slug(item.slug)
            if existing is None:
                self._wallet_repo._session.add(item)
                continue
            existing.title = item.title
            existing.description = item.description
            existing.price = item.price
            existing.kind = item.kind
            existing.meta = item.meta
            existing.sort_order = item.sort_order
            existing.is_active = True
        await self._wallet_repo._session.flush()
        return await self._store.list_active_items()
