"""Registry-driven equality / copy / hash-consistency sweep over every model.

`TOMBase.__eq__` is hash-based (`a == b` iff `a.hash() == b.hash()`) and `__hash__`
returns an int digest of the same `_hash_repr`. The mutation-safety design relies on
`model_copy(deep=True)` yielding an equal-but-independent object. These invariants are
swept over the bare instances from `_sweep_helpers`, so new models are covered
automatically.

Invariant 5 (mutation inequality) is best-effort: it mutates one declared scalar field
and checks the hash responds. Models with no declared str/int/bool scalar field are
skipped for that sub-check (documented via the skip reason). For models with a default
`_hash_repr` (which hashes every declared field) *every* scalar must change the hash; for
models with a custom `_hash_repr` only one scalar need respond, since a custom repr may
intentionally exclude descriptive fields (e.g. `MetaAttribute.constraint_name`).
"""

from __future__ import annotations

import enum
import types
from typing import Any, Literal, Union, get_args, get_origin

import pytest
from _sweep_helpers import sweep_id, MODELS, build, unwrap

from translator_tom import TOMBase


def _scalar_kind(ann: Any) -> type | None:
    """Resolve `ann` to `str`/`int`/`bool` if it is (or unions to) a plain scalar.

    Literals and enums return None: their value set is constrained, so they are not
    reliable free-mutation targets.
    """
    ann = unwrap(ann)
    origin = get_origin(ann)
    if origin is Union or origin is types.UnionType:
        for member in get_args(ann):
            if member is type(None):
                continue
            if (kind := _scalar_kind(member)) is not None:
                return kind
        return None
    if origin is Literal:
        return None
    if isinstance(ann, type) and not issubclass(ann, enum.Enum):
        for scalar in (bool, int, str):  # bool before int (bool is an int subclass)
            if issubclass(ann, scalar):
                return scalar
    return None


def _scalar_fields(model: type[TOMBase]) -> list[tuple[str, type]]:
    """Declared str/int/bool fields, in declaration order."""
    fields = []
    for name, field in model.model_fields.items():
        if (kind := _scalar_kind(field.annotation)) is not None:
            fields.append((name, kind))
    return fields


def _distinct_value(kind: type, current: object) -> object:
    """A value of `kind` guaranteed to differ from `current`."""
    if kind is bool:
        return (not current) if isinstance(current, bool) else True
    if kind is int:
        return (current + 1) if isinstance(current, int) else 1
    return (current + "_sweep_mut") if isinstance(current, str) else "sweep_mut"


@pytest.mark.parametrize("model", MODELS, ids=[sweep_id(m) for m in MODELS])
def test_reflexivity(model: type[TOMBase]) -> None:
    """1. `m == m` and `hash(m) == hash(m)`."""
    m = build(model)
    assert m == m  # noqa: PLR0124
    assert hash(m) == hash(m)


@pytest.mark.parametrize("model", MODELS, ids=[sweep_id(m) for m in MODELS])
def test_identical_builds_equal(model: type[TOMBase]) -> None:
    """2. Two identical bare builds are equal and hash-equal."""
    a = build(model)
    b = build(model)
    assert a == b
    assert a.hash() == b.hash()
    assert hash(a) == hash(b)


@pytest.mark.parametrize("model", MODELS, ids=[sweep_id(m) for m in MODELS])
def test_deep_copy_equality(model: type[TOMBase]) -> None:
    """3. A deep copy is equal, hash-equal, and a distinct object."""
    m = build(model)
    c = m.model_copy(deep=True)
    assert c == m
    assert c.hash() == m.hash()
    assert c is not m  # model_copy always yields a fresh instance


@pytest.mark.parametrize("model", MODELS, ids=[sweep_id(m) for m in MODELS])
def test_hash_eq_iff_eq(model: type[TOMBase]) -> None:
    """4. For the identical pair, `(a == b) == (a.hash() == b.hash())` (both True)."""
    a = build(model)
    b = build(model)
    assert (a == b) is True
    assert (a.hash() == b.hash()) is True
    assert (a == b) == (a.hash() == b.hash())


@pytest.mark.parametrize("model", MODELS, ids=[sweep_id(m) for m in MODELS])
def test_mutation_changes_hash(model: type[TOMBase]) -> None:
    """5. Mutating a declared scalar field makes the copy unequal and re-hashes.

    Best-effort: a default `_hash_repr` must react to *every* declared scalar (any that
    does not is a field wrongly excluded from the hash); a custom `_hash_repr` need only
    react to one, since it may intentionally drop descriptive fields.
    """
    scalars = _scalar_fields(model)
    if not scalars:
        pytest.skip("no declared str/int/bool scalar field to mutate")

    m = build(model)
    base = m.hash()
    default_hash = type(m)._hash_repr is TOMBase._hash_repr
    responsive = []
    for name, kind in scalars:
        mutated = m.model_copy(deep=True)
        setattr(mutated, name, _distinct_value(kind, getattr(mutated, name, None)))
        if mutated.hash() != base:
            assert mutated != m
            assert hash(mutated) != hash(m)
            responsive.append(name)
        elif default_hash:
            pytest.fail(
                f"{model.__name__}.{name}: default _hash_repr omits a declared scalar"
            )
    assert responsive, f"{model.__name__}: no declared scalar affects the hash"
