from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import Depends

from app.api.service_deps_internal.container import ServiceContainer, get_service_container
from app.api.service_deps_internal.registry import SERVICE_BINDINGS, ServiceBinding

ServiceProvider = Callable[..., Any]


def _make_provider(binding: ServiceBinding) -> ServiceProvider:
    def provider(
        container: ServiceContainer = Depends(get_service_container),
        *,
        _attr: str = binding.container_attr,
    ) -> Any:
        return getattr(container, _attr)

    provider.__name__ = f"get_{binding.name}_service"
    provider.__qualname__ = provider.__name__
    provider.__doc__ = f"Resolve `{binding.container_attr}` from the request container."
    return provider


_generated_names: list[str] = []
for _binding in SERVICE_BINDINGS:
    _name = f"get_{_binding.name}_service"
    globals()[_name] = _make_provider(_binding)
    _generated_names.append(_name)

__all__ = tuple(_generated_names)

del _binding
del _generated_names
del _name

