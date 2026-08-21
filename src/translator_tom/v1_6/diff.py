from __future__ import annotations

__all__ = ["Delta", "diff"]

from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal, TypeVar, cast

from translator_tom.v1_6 import (
    Analysis,
    Attribute,
    AuxiliaryGraph,
    BaseAnalysis,
    Edge,
    EdgeBinding,
    Message,
    NodeBinding,
    PathBinding,
    PathfinderAnalysis,
    Qualifier,
    Response,
    Result,
    RetrievalSource,
    TOMBase,
    tomhash,
)

T = TypeVar("T", bound=TOMBase)

Kind = Literal["added", "removed", "changed", "reordered"]


@dataclass(frozen=True)
class Delta:
    """A single located difference between two objects.

    ``path`` is the structural path to the difference; segments are field names, dict
    keys, or — for members of order-insensitively aligned lists — the member's identity
    locator (a positional index would be meaningless after alignment). ``left`` is the
    baseline value, ``right`` the new value; ``left`` is ``None`` for ``added`` and
    ``right`` is ``None`` for ``removed``. ``locator`` is a short human-readable identity
    label for the entity the delta concerns, when one is determinable.
    """

    path: tuple[str | int, ...]
    kind: Kind
    left: Any = None
    right: Any = None
    locator: str | None = None


##### Identity & description (diff-local, keyed by type — never on the models) #####


def _analysis_identity(analysis: Analysis) -> object:
    """Coarse identity for an Analysis: resource + edge bindings, but not score/attributes."""
    return (
        "Analysis",
        analysis.resource_id,
        frozenset(
            (qedge, frozenset(b.hash() for b in bindings))
            for qedge, bindings in analysis.edge_bindings.items()
        ),
    )


def _pathfinder_identity(analysis: PathfinderAnalysis) -> object:
    """Coarse identity for a PathfinderAnalysis: resource + path bindings, not score."""
    return (
        "PathfinderAnalysis",
        analysis.resource_id,
        frozenset(
            (qpath, frozenset(b.hash() for b in bindings))
            for qpath, bindings in analysis.path_bindings.items()
        ),
    )


def _attribute_identity(attribute: Attribute) -> object:
    """Coarse identity for an Attribute: its type, not its value."""
    return ("Attribute", attribute.attribute_type_id, attribute.value_type_id)


def _auxgraph_identity(aux: AuxiliaryGraph) -> object:
    """Coarse identity for an AuxiliaryGraph: its edge set, not its attributes."""
    return ("AuxiliaryGraph", frozenset(aux.edges))


# Coarse alignment keys, looked up by exact type. A coarser key than .hash() lets a
# re-scored analysis / changed-value attribute pair up and report as one `changed` delta
# instead of an add+remove pair. Unregistered types fall back to .hash() (see _identity_key).
_IDENTITY: dict[type, Callable[[Any], object]] = {
    Analysis: _analysis_identity,
    PathfinderAnalysis: _pathfinder_identity,
    Attribute: _attribute_identity,
    AuxiliaryGraph: _auxgraph_identity,
}


def _hash_key(value: object) -> str:
    """Exact identity key used for the first alignment pass."""
    return value.hash() if isinstance(value, TOMBase) else tomhash(value)


def _identity_key(value: object) -> object:
    """Coarse identity key used for the second alignment pass (registry, else .hash())."""
    fn = _IDENTITY.get(type(value))
    if fn is not None:
        return fn(value)
    return _hash_key(value)


def _short(value: object, limit: int = 40) -> str:
    """A compact, truncated one-line string for a scalar value."""
    text = str(value)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _describe(value: object) -> str:  # noqa: PLR0911
    """A short, stable identity label for an aligned entity, used in paths and locators."""
    if isinstance(value, Edge):
        return f"{value.subject} --{value.predicate}--> {value.object}"
    if isinstance(value, Result):
        return ",".join(
            f"{qnode}={'|'.join(b.id for b in value.node_bindings[qnode])}"
            for qnode in sorted(value.node_bindings)
        )
    if isinstance(value, BaseAnalysis):
        return f"{value.resource_id}@{value.score}"
    if isinstance(value, (NodeBinding, EdgeBinding, PathBinding)):
        return str(value.id)
    if isinstance(value, Attribute):
        return str(value.attribute_type_id)
    if isinstance(value, RetrievalSource):
        return f"{value.resource_id}({value.resource_role})"
    if isinstance(value, Qualifier):
        return f"{value.qualifier_type_id}={value.qualifier_value}"
    if isinstance(value, TOMBase):
        return f"{type(value).__name__}#{value.hash()[:8]}"
    return _short(value)


def _jsonable(value: object) -> Any:
    """Convert a value (possibly holding TOM models) to a JSON-serializable form."""
    if isinstance(value, TOMBase):
        return value.to_dict()
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in cast("dict[Any, Any]", value).items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in cast("list[Any]", value)]
    return value


##### Alignment & recursion #####


def _align_list(
    left: list[Any], right: list[Any]
) -> tuple[list[Any], list[Any], list[tuple[Any, Any]]]:
    """Align two lists as multisets, order-insensitively.

    Two passes: first pair members with equal ``.hash()`` (exact), then pair the leftovers
    by coarse ``_identity_key`` so a changed volatile field (score, attribute value) yields
    a matched pair to descend into rather than an add+remove. Returns
    ``(removed, added, matched_pairs)``.
    """

    def _bucket(
        items: list[Any], key: Callable[[Any], object]
    ) -> dict[object, deque[Any]]:
        buckets: dict[object, deque[Any]] = defaultdict(deque)
        for item in items:
            buckets[key(item)].append(item)
        return buckets

    matched: list[tuple[Any, Any]] = []

    # Pass 1: exact, by full hash.
    left_by_hash = _bucket(left, _hash_key)
    right_by_hash = _bucket(right, _hash_key)
    left_rest: list[Any] = []
    for key, lefts in left_by_hash.items():
        rights = right_by_hash.get(key, deque())
        while lefts and rights:
            matched.append((lefts.popleft(), rights.popleft()))
        left_rest.extend(lefts)
    right_rest = [item for rights in right_by_hash.values() for item in rights]

    # Pass 2: coarse, by identity key, on the leftovers only.
    left_by_id = _bucket(left_rest, _identity_key)
    right_by_id = _bucket(right_rest, _identity_key)
    removed: list[Any] = []
    for key, lefts in left_by_id.items():
        rights = right_by_id.get(key, deque())
        while lefts and rights:
            matched.append((lefts.popleft(), rights.popleft()))
        removed.extend(lefts)
    added = [item for rights in right_by_id.values() for item in rights]

    return removed, added, matched


def _diff_value(
    path: tuple[str | int, ...], left: Any, right: Any, *, strict: bool
) -> list[Delta]:
    """Recursively diff two values, aligning unordered lists by identity."""
    if type(left) is not type(right):
        return [
            Delta(path, "changed", _jsonable(left), _jsonable(right), _describe(left))
        ]
    if isinstance(left, TOMBase):
        return _diff_model(path, left, cast("TOMBase", right), strict=strict)
    if isinstance(left, dict):
        return _diff_dict(path, left, cast("dict[Any, Any]", right), strict=strict)
    if isinstance(left, list):
        return _diff_list(path, left, cast("list[Any]", right), strict=strict)
    if left != right:
        return [Delta(path, "changed", left, right)]
    return []


def _diff_model(
    path: tuple[str | int, ...], left: TOMBase, right: TOMBase, *, strict: bool
) -> list[Delta]:
    """Diff two models; ``strict=False`` short-circuits on equal ``.hash()``.

    Declared fields are compared structurally. Extra (non-declared) fields are opaque
    JSON we don't descend into, so any extra key present on either side is reported as a
    single ``changed`` delta carrying both raw values (either may be ``None`` if absent).
    """
    if not strict and left.hash() == right.hash():
        return []
    deltas: list[Delta] = [
        d
        # same type => same declared fields, always present on both instances
        for name in left.__pydantic_fields__
        for d in _diff_value(
            (*path, name), getattr(left, name), getattr(right, name), strict=strict
        )
    ]
    deltas.extend(
        Delta(
            (*path, name),
            "changed",
            _jsonable(left.extra_dict.get(name)),
            _jsonable(right.extra_dict.get(name)),
            _describe(left),
        )
        for name in sorted(set(left.extra_dict) | set(right.extra_dict))
    )
    return deltas


def _is_auxgraph_dict(value: dict[Any, Any]) -> bool:
    """True for a non-empty dict whose values are AuxiliaryGraphs (arbitrary keys)."""
    return len(value) > 0 and isinstance(next(iter(value.values())), AuxiliaryGraph)


def _diff_dict(
    path: tuple[str | int, ...],
    left: dict[Any, Any],
    right: dict[Any, Any],
    *,
    strict: bool,
) -> list[Delta]:
    """Diff two dicts by key — except aux-graph dicts, aligned by value content."""
    if _is_auxgraph_dict(left) or _is_auxgraph_dict(right):
        return _diff_list(
            path, list(left.values()), list(right.values()), strict=strict
        )

    deltas: list[Delta] = []
    for key in sorted(left.keys() - right.keys()):
        val = left[key]
        deltas.append(
            Delta((*path, key), "removed", left=_jsonable(val), locator=_describe(val))
        )
    for key in sorted(right.keys() - left.keys()):
        val = right[key]
        deltas.append(
            Delta((*path, key), "added", right=_jsonable(val), locator=_describe(val))
        )
    for key in sorted(left.keys() & right.keys()):
        deltas.extend(_diff_value((*path, key), left[key], right[key], strict=strict))
    return deltas


def _diff_list(
    path: tuple[str | int, ...], left: list[Any], right: list[Any], *, strict: bool
) -> list[Delta]:
    """Diff two lists as unordered multisets, aligning members by identity."""
    removed, added, matched = _align_list(left, right)
    deltas: list[Delta] = [
        Delta(
            (*path, _describe(item)),
            "removed",
            left=_jsonable(item),
            locator=_describe(item),
        )
        for item in removed
    ]
    deltas.extend(
        Delta(
            (*path, _describe(item)),
            "added",
            right=_jsonable(item),
            locator=_describe(item),
        )
        for item in added
    )
    changed = False
    for lit, rit in matched:
        sub = _diff_value((*path, _describe(lit)), lit, rit, strict=strict)
        if sub:
            changed = True
            deltas.extend(sub)

    # Reorder is a signal only for model-element lists; scalar order is meaningless in TRAPI.
    if (
        not removed
        and not added
        and not changed
        and left
        and isinstance(left[0], TOMBase)
        and [_hash_key(x) for x in left] != [_hash_key(x) for x in right]
    ):
        deltas.append(
            Delta(
                path,
                "reordered",
                left=[_describe(x) for x in left],
                right=[_describe(x) for x in right],
            )
        )
    return deltas


def _normalized(obj: TOMBase) -> TOMBase:
    """Return a normalized deep copy (edges re-keyed by hash, references remapped).

    Only Message and Response can be normalized; other types raise.
    """
    if isinstance(obj, Response):
        obj = obj.model_copy(deep=True)
        obj.message.normalize()
        return obj
    if isinstance(obj, Message):
        obj = obj.model_copy(deep=True)
        obj.normalize()
        return obj
    raise ValueError("normalize=True requires Message or Response inputs.")


def diff(a: T, b: T, *, strict: bool = True, normalize: bool = False) -> list[Delta]:
    """Find the differences between two objects, as order-insensitive deltas.

    Lists are aligned as multisets by member identity (not by position), so reordering
    unordered TRAPI collections produces no spurious diffs; a genuine reorder of a
    model-element list is reported as a single ``reordered`` delta.

    Args:
        a: Baseline object (the ``left`` side of each delta).
        b: New object (the ``right`` side of each delta).
        strict: When True (default), descend into every field and report every
            field-level difference. When False, short-circuit any subtree whose
            ``.hash()`` matches, ignoring fields that hashing excludes (e.g.
            ``Edge.hash()`` ignores ``attributes``).
        normalize: When True, compare normalized deep copies of the inputs (edges
            re-keyed by hash, references remapped) so arbitrary per-service edge ids
            don't matter; the caller's objects are never mutated. Only valid for
            ``Message``/``Response`` inputs; raises otherwise. Defaults to False.

    Returns:
        The list of ``Delta`` differences (empty when the objects are equivalent).

    Raises:
        ValueError: If ``a`` and ``b`` are different types, or ``normalize=True`` is
            given for a non-``Message``/``Response`` input.
    """
    if type(a) is not type(b):
        raise ValueError("Cannot compare different object types.")
    if normalize:
        a = cast("T", _normalized(a))
        b = cast("T", _normalized(b))
    return _diff_value((), a, b, strict=strict)
