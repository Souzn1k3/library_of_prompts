from __future__ import annotations

import uuid
from urllib.parse import urljoin, urlparse

from app.core.client_tokens import candidate_scoped_tokens, scoped_or_random_token
from app.core.errors import AppError
from app.infrastructure.db.models import MarketplaceTransactionKind, PromptAccessSource, PromptPurchase
from app.modules.marketplace.model.marketplace import PromptPurchaseRead
from app.modules.marketplace.service.marketplace_checkout_shared import stripe
from app.modules.marketplace.service.policy import settlement_available_at


class MarketplaceCheckoutHelperMixin:
    @staticmethod
    def _initial_settlement_status(
        *,
        seller_amount_rub: int,
        seller_amount_lumens: int,
        completed_at,
    ):
        if seller_amount_rub <= 0 and seller_amount_lumens <= 0:
            from app.infrastructure.db.models import MarketplaceSettlementStatus

            return MarketplaceSettlementStatus.available, completed_at
        from app.infrastructure.db.models import MarketplaceSettlementStatus

        return MarketplaceSettlementStatus.pending, settlement_available_at(completed_at)

    @staticmethod
    def _client_token_scope(user_id: uuid.UUID, client_token: str, *, prefix: str) -> str:
        return f"{prefix}:{user_id}:{client_token}".lower()

    def _scoped_client_token(self, user_id: uuid.UUID, client_token: str | None, *, prefix: str) -> str:
        return scoped_or_random_token(user_id, client_token, prefix=prefix)

    def _candidate_client_tokens(self, user_id: uuid.UUID, client_token: str, *, prefix: str) -> list[str]:
        return candidate_scoped_tokens(user_id, client_token, prefix=prefix)

    async def _find_purchase_by_client_token(
        self,
        *,
        user_id: uuid.UUID,
        client_token: str,
        prefix: str,
    ) -> PromptPurchase | None:
        for token in self._candidate_client_tokens(user_id, client_token, prefix=prefix):
            purchase = await self._repo.get_purchase_by_client_token(user_id=user_id, client_token=token)
            if purchase is not None:
                return purchase
        return None

    @staticmethod
    def _redirect_origin(url: str) -> str | None:
        parsed = urlparse(url)
        if parsed.scheme.lower() not in {"http", "https"}:
            return None
        if not parsed.hostname or parsed.username or parsed.password:
            return None
        port = parsed.port
        if port is None:
            port = 443 if parsed.scheme.lower() == "https" else 80
        return f"{parsed.scheme.lower()}://{parsed.hostname.lower()}:{port}"

    def _allowed_checkout_redirect_origins(self) -> set[str]:
        urls = list(self._settings.cors_origin_list)
        urls.extend(
            [
                self._settings.billing_checkout_success_url,
                self._settings.billing_checkout_cancel_url,
                self._settings.billing_portal_return_url,
            ]
        )
        out: set[str] = set()
        for url in urls:
            origin = self._redirect_origin(url)
            if origin:
                out.add(origin)
        return out

    def _resolve_checkout_redirect_url(self, candidate: str | None, *, default_url: str) -> str:
        raw = (candidate or "").strip()
        if not raw:
            return default_url

        parsed = urlparse(raw)
        if not parsed.scheme and not parsed.netloc:
            if not raw.startswith("/") or raw.startswith("//"):
                raise AppError(
                    code="invalid_redirect_url",
                    status_code=400,
                    message="This redirect URL is not allowed.",
                )
            raw = urljoin(default_url, raw)

        origin = self._redirect_origin(raw)
        if origin is None or origin not in self._allowed_checkout_redirect_origins():
            raise AppError(
                code="invalid_redirect_url",
                status_code=400,
                message="This redirect URL is not allowed.",
            )
        return raw

    def _stripe_checkout_enabled(self) -> bool:
        return bool(stripe and self._settings.stripe_secret_key)

    def _to_purchase_read(self, purchase: PromptPurchase, *, can_review: bool | None = None) -> PromptPurchaseRead:
        return self._purchase_to_read(purchase, can_review)

    async def _ensure_purchase_entitlement(
        self,
        *,
        user_id: uuid.UUID,
        prompt_id: uuid.UUID,
        purchase_id: uuid.UUID,
        source: PromptAccessSource,
        payment_method: str,
        granted_at,
        meta: dict[str, object] | None = None,
    ) -> None:
        entitlement = await self._repo.try_create_entitlement(
            user_id=user_id,
            prompt_id=prompt_id,
            source=source,
            purchase_id=purchase_id,
            meta={"payment_method": payment_method, **(meta or {})},
            granted_at=granted_at,
        )
        if entitlement is None:
            entitlement = await self._repo.get_entitlement(
                user_id=user_id,
                prompt_id=prompt_id,
                for_update=True,
            )
            if entitlement is None:
                raise RuntimeError("Failed to ensure purchase entitlement")

    async def _record_purchase_transactions(
        self,
        *,
        purchase_id: uuid.UUID,
        prompt_id: uuid.UUID,
        buyer_user_id: uuid.UUID,
        seller_user_id: uuid.UUID | None,
        currency_code: str,
        buyer_amount: int,
        fee_amount: int,
        seller_amount: int,
        meta: dict[str, object] | None = None,
    ) -> None:
        payload = dict(meta or {})
        await self._repo.create_marketplace_transaction(
            prompt_purchase_id=purchase_id,
            prompt_id=prompt_id,
            actor_user_id=buyer_user_id,
            kind=MarketplaceTransactionKind.buyer_charge,
            currency_code=currency_code,
            amount=buyer_amount,
            meta=payload,
        )
        await self._repo.create_marketplace_transaction(
            prompt_purchase_id=purchase_id,
            prompt_id=prompt_id,
            actor_user_id=None,
            kind=MarketplaceTransactionKind.platform_fee,
            currency_code=currency_code,
            amount=fee_amount,
            meta=payload,
        )
        if seller_user_id is not None and seller_amount > 0:
            await self._repo.create_marketplace_transaction(
                prompt_purchase_id=purchase_id,
                prompt_id=prompt_id,
                actor_user_id=seller_user_id,
                kind=MarketplaceTransactionKind.seller_credit,
                currency_code=currency_code,
                amount=seller_amount,
                meta=payload,
            )
