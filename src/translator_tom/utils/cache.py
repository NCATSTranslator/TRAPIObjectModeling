from __future__ import annotations

import copy
from collections.abc import Callable
from functools import lru_cache, wraps
from typing import ParamSpec, TypeVar

__all__ = ["lru_copy_cache"]

_P = ParamSpec("_P")
_R = TypeVar("_R")


def lru_copy_cache(
    maxsize: int | None = 128,
    *,
    copier: Callable[[_R], _R] = copy.copy,
) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
    """Like `functools.lru_cache`, but copy the cached result for mutable safety.

    `copier` defaults to a shallow `copy.copy`. Pass `copy.deepcopy` for nested mutables. `cache_clear`/`cache_info` are exposed as usual.
    """

    def decorator(func: Callable[_P, _R]) -> Callable[_P, _R]:
        cached = lru_cache(maxsize=maxsize)(func)

        @wraps(func)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            return copier(cached(*args, **kwargs))

        wrapper.cache_clear = cached.cache_clear  # ty: ignore[unresolved-attribute]
        wrapper.cache_info = cached.cache_info  # ty: ignore[unresolved-attribute]
        return wrapper

    return decorator
