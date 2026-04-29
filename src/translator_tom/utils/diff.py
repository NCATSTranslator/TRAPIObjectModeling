from typing import Any, TypeVar, cast

from stablehash import stablehash

from translator_tom import TOMBaseObject

T = TypeVar("T", bound=TOMBaseObject)


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

        if isinstance(value_a, TOMBaseObject):
            if not strict:
                hash_a = value_a.hash()
                hash_b = cast("TOMBaseObject", value_b).hash()
                if hash_a == hash_b:
                    continue
        else:
            hash_a = stablehash(value_a).hexdigest()
            hash_b = stablehash(value_b).hexdigest()
            if hash_a == hash_b:
                continue

        if isinstance(value_a, TOMBaseObject):
            stack.extend(
                (
                    (*path, field),
                    getattr(value_a, field),
                    getattr(value_b, field),
                )
                for field in value_a.__pydantic_fields__
            )
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
        else:
            differing.append(path)

    return differing
