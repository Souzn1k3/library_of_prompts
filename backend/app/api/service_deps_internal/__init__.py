from __future__ import annotations

from app.api.service_deps_internal import builders as _builders
from app.api.service_deps_internal import providers as _providers
from app.api.service_deps_internal.container import ServiceContainer, _container, get_service_container

for _name in _builders.__all__:
    globals()[_name] = getattr(_builders, _name)

for _name in _providers.__all__:
    globals()[_name] = getattr(_providers, _name)

__all__ = (
    "ServiceContainer",
    "_container",
    "get_service_container",
    *_builders.__all__,
    *_providers.__all__,
)

del _name

