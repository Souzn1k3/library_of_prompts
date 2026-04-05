from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.service_deps_internal.container import _container
from app.api.service_deps_internal.registry import SERVICE_BINDINGS, ServiceBinding

ServiceBuilder = Callable[[AsyncSession], Any]


def _make_builder(binding: ServiceBinding) -> ServiceBuilder:
    def builder(session: AsyncSession, *, _attr: str = binding.container_attr) -> Any:
        return getattr(_container(session), _attr)

    builder.__name__ = f"build_{binding.name}_service"
    builder.__qualname__ = builder.__name__
    builder.__doc__ = f"Build `{binding.container_attr}` from an async session."
    return builder


_generated_names: list[str] = []
for _binding in SERVICE_BINDINGS:
    _name = f"build_{_binding.name}_service"
    globals()[_name] = _make_builder(_binding)
    _generated_names.append(_name)

__all__ = tuple(_generated_names)

del _binding
del _generated_names
del _name

