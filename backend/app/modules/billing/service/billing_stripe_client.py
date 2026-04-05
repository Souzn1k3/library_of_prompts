from __future__ import annotations

from typing import Any

_stripe_module: Any | None
try:
    import stripe as _stripe_module
except Exception:  # pragma: no cover - optional runtime dependency
    _stripe_module = None

stripe: Any = _stripe_module
