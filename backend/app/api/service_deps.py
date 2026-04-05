from __future__ import annotations

from app.api import service_deps_internal as _internal

for _name in _internal.__all__:
    globals()[_name] = getattr(_internal, _name)

__all__ = tuple(_internal.__all__)

del _name

