from __future__ import annotations

import hashlib
import uuid


ECONOMY_EXPERIMENT_NAME = "economy_loop_v2"
ECONOMY_EXPERIMENT_CONTROL = "control"
ECONOMY_EXPERIMENT_TREATMENT = "treatment"


def economy_experiment_variant(*, user_id: uuid.UUID, payer_status: str) -> str:
    segment = "payer" if payer_status == "payer" else "non_payer"
    seed = f"{ECONOMY_EXPERIMENT_NAME}:{segment}:{user_id}"
    bucket = int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8], 16) % 2
    return ECONOMY_EXPERIMENT_CONTROL if bucket == 0 else ECONOMY_EXPERIMENT_TREATMENT


def economy_experiment_metadata(*, user_id: uuid.UUID, payer_status: str) -> dict[str, str]:
    return {
        "experiment_name": ECONOMY_EXPERIMENT_NAME,
        "experiment_variant": economy_experiment_variant(user_id=user_id, payer_status=payer_status),
        "payer_status": "payer" if payer_status == "payer" else "non_payer",
    }

