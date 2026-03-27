"""Build Stripe-compatible webhook signatures (same algorithm as stripe.WebhookSignature)."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any


def sign_stripe_webhook_payload(*, payload_bytes: bytes, secret: str) -> str:
    """Return a valid Stripe-Signature header value for the given raw body and signing secret."""
    payload = payload_bytes.decode("utf-8")
    timestamp = int(time.time())
    signed_payload = f"{timestamp}.{payload}"
    digest = hmac.new(
        secret.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"t={timestamp},v1={digest}"


def subscription_updated_event(
    *,
    event_id: str,
    customer_id: str,
    subscription_id: str,
    tier: str,
    status: str = "active",
) -> dict[str, Any]:
    now = int(time.time())
    return {
        "id": event_id,
        "object": "event",
        "type": "customer.subscription.updated",
        "created": now,
        "data": {
            "object": {
                "id": subscription_id,
                "object": "subscription",
                "customer": customer_id,
                "status": status,
                "metadata": {"tier": tier},
                "items": {
                    "data": [
                        {
                            "price": {
                                "id": "price_test_placeholder",
                            },
                        },
                    ],
                },
                "current_period_start": now,
                "current_period_end": now + 86400 * 30,
                "trial_end": None,
                "cancel_at_period_end": False,
                "canceled_at": None,
            },
        },
    }


def event_json_bytes(event: dict[str, Any]) -> bytes:
    return json.dumps(event, separators=(",", ":"), sort_keys=True).encode("utf-8")
