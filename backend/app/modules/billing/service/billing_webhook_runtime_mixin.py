from __future__ import annotations

import hashlib

from app.core.errors import AppError
from app.core.logging import get_logger
from app.infrastructure.db.models import BillingProvider
from app.modules.billing.service.billing_stripe_client import stripe
from app.modules.billing.service.billing_utils import stripe_object_to_dict

log = get_logger(__name__)


class BillingWebhookRuntimeMixin:
    async def handle_webhook(
        self,
        *,
        payload: bytes,
        signature_header: str | None,
    ) -> dict[str, str]:
        if not self._stripe_webhook_enabled():
            log.warning("billing_webhook_failed", reason="not_configured")
            raise AppError(
                code="billing_not_configured",
                status_code=501,
                message="Payment updates are currently unavailable.",
                message_key="errors.billing_not_configured",
            )
        if not signature_header:
            log.warning(
                "billing_webhook_failed",
                observability_event="billing_webhook_signature_missing",
                reason="missing_signature",
            )
            raise AppError(
                code="invalid_webhook_signature",
                status_code=400,
                message="We couldn't verify this payment update.",
                message_key="errors.invalid_webhook_signature",
            )
        assert stripe is not None
        stripe.api_key = self._settings.stripe_secret_key
        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=signature_header,
                secret=self._settings.stripe_webhook_secret,
            )
        except Exception as exc:
            log.warning(
                "billing_webhook_failed",
                observability_event="billing_webhook_signature_invalid",
                reason="invalid_signature",
                error_type=type(exc).__name__,
            )
            raise AppError(
                code="invalid_webhook_signature",
                status_code=400,
                message="We couldn't verify this payment update.",
                message_key="errors.invalid_webhook_signature",
            ) from exc

        event_dict = stripe_object_to_dict(event)
        event_id = str(event_dict.get("id") or "")
        if not event_id:
            log.warning("billing_webhook_failed", reason="missing_event_id")
            raise AppError(
                code="invalid_webhook_payload",
                status_code=400,
                message="We couldn't process this payment update.",
                message_key="errors.invalid_webhook_payload",
            )
        payload_hash = hashlib.sha256(payload).hexdigest()
        claim_id = await self._repo.try_claim_webhook_event(
            provider=BillingProvider.stripe,
            event_id=event_id,
            payload_hash=payload_hash,
        )
        if claim_id is None:
            log.info(
                "billing_webhook_duplicate",
                observability_event="billing_webhook_duplicate",
                stripe_event_id=event_id,
            )
            return {"status": "duplicate"}

        try:
            await self._process_stripe_event(event_dict)
        except Exception:
            await self._repo.delete_webhook_claim(claim_id=claim_id)
            log.exception(
                "billing_webhook_failed",
                observability_event="billing_webhook_processing_error",
                reason="processing_error",
                stripe_event_id=event_id,
                stripe_event_type=str(event_dict.get("type") or ""),
            )
            raise AppError(
                code="webhook_processing_failed",
                status_code=500,
                message="We couldn't complete this payment update.",
            ) from None
        return {"status": "ok"}
