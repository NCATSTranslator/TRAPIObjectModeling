from __future__ import annotations

__all__ = ["diff"]

from typing import Any, TypeVar, cast

from translator_tom import TOMBase

T = TypeVar("T", bound=TOMBase)


def diff(a: T, b: T, *, strict: bool = True) -> list[tuple[str | int, ...]]:
    """Find the items that differ between the two given objects.

    Args:
        a: First object to compare.
        b: Second object to compare.
        strict: When True (default), descend into every field and compare
            structurally. When False, use TRAPI ``.hash()`` rules to
            short-circuit equal subtrees, which may ignore fields that the
            object's hashing semantics exclude (e.g. ``Edge.hash()`` ignores
            ``attributes``).

    Note:
        Extra (non-declared) fields present on either side are always reported
        as differing; their arbitrary-JSON values are never descended into or
        compared.
    """
    if type(a) is not type(b):
        raise ValueError("Cannot compare different object types.")

    differing: list[tuple[str | int, ...]] = []
    stack: list[tuple[tuple[str | int, ...], Any, Any]] = [((), a, b)]

    while stack:
        path, value_a, value_b = stack.pop()

        if type(value_a) is not type(value_b):
            differing.append(path)
            continue

        # short-circuit equal model subtrees via .hash() when not strict
        if (
            isinstance(value_a, TOMBase)
            and not strict
            and value_a.hash() == cast("TOMBase", value_b).hash()
        ):
            continue

        if isinstance(value_a, TOMBase):
            stack.extend(
                (
                    (*path, field),
                    getattr(value_a, field),
                    getattr(value_b, field),
                )
                for field in value_a.__pydantic_fields__
            )
            # extra values are arbitrary JSON; mark keys differing without comparing
            extra_keys = set(value_a.extra_dict) | set(
                cast("TOMBase", value_b).extra_dict
            )
            differing.extend((*path, key) for key in extra_keys)
        elif isinstance(value_a, dict):
            dict_a = cast("dict[Any, Any]", value_a)
            dict_b = cast("dict[Any, Any]", value_b)
            keys_a = set(dict_a)
            keys_b = set(dict_b)
            differing.extend((*path, key) for key in keys_a ^ keys_b)
            stack.extend(
                ((*path, key), dict_a[key], dict_b[key]) for key in keys_a & keys_b
            )
        elif isinstance(value_a, list):
            list_a = cast("list[Any]", value_a)
            list_b = cast("list[Any]", value_b)
            len_a, len_b = len(list_a), len(list_b)
            common = min(len_a, len_b)
            stack.extend(((*path, i), list_a[i], list_b[i]) for i in range(common))
            differing.extend((*path, i) for i in range(common, max(len_a, len_b)))
        # scalar leaf: compare directly
        elif value_a != value_b:
            differing.append(path)

    return differing
