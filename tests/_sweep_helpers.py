"""Shared harness for the reflection-driven `test_sweep_*` suites.

`MODELS`/`DICTUTILS` are collected from the public API + the `DictUtil` registry, and
`build()` makes a bare, minimal instance of any model from its field annotations. Each
cross-cutting invariant (hash, round-trip, parity, equality, coverage, serialization)
gets its own `test_sweep_*.py` that imports these, so new models are covered automatically.
"""

from __future__ import annotations

import enum
import types
from typing import Any, Literal, Union, get_args, get_origin

import translator_tom
import translator_tom.model_dicts  # noqa: F401  (import populates the DictUtil registry)
from translator_tom import TOMBase
from translator_tom.utils.dict_util_base import DictUtil


def unwrap(ann: Any) -> Any:
    """Strip `Annotated[X, ...]` down to `X`."""
    while hasattr(ann, "__metadata__"):
        ann = ann.__origin__
    return ann


def dummy(ann: Any) -> Any:
    """Return a minimal, type-correct value for a field annotation (validation skipped)."""
    ann = unwrap(ann)
    origin = get_origin(ann)
    if origin is Union or origin is types.UnionType:
        members = [a for a in get_args(ann) if a is not type(None)]
        return dummy(members[0]) if members else None
    if origin is list:  # one element, to satisfy min_length lists (e.g. Edge.sources)
        elems = get_args(ann)
        return [dummy(elems[0])] if elems else []
    if origin in (set, frozenset, tuple):
        return []
    if origin is dict:
        return {}
    if origin is Literal:
        return get_args(ann)[0]
    if isinstance(ann, type):
        if issubclass(ann, TOMBase):
            return build(ann)
        if issubclass(ann, enum.Enum):
            return next(iter(ann))
        if issubclass(ann, bool):
            return False
        if issubclass(ann, int):  # bool handled above; float below (int is not a float subclass)
            return 0
        if issubclass(ann, float):
            return 0.0
        if issubclass(ann, str):
            return "x"
    return "x"  # Any / unresolved


def build(model: type[TOMBase]) -> TOMBase:
    """A bare, unvalidated instance with only required fields filled by `dummy`."""
    values = {
        name: dummy(field.annotation)
        for name, field in model.model_fields.items()
        if field.is_required()
    }
    return model.model_construct(**values)


MODELS = sorted(
    {
        obj
        for name in translator_tom.__all__
        if isinstance((obj := getattr(translator_tom, name)), type)
        and issubclass(obj, TOMBase)
        and obj is not TOMBase
    },
    key=lambda c: c.__name__,
)

# Filter to product DictUtils: test modules define throwaway DictUtil subclasses that
# register into the class-level registry, and collection order would otherwise leak them
# into every sweep. Restricting by module keeps DICTUTILS deterministic.
DICTUTILS = sorted(
    (
        (model, du)
        for model, du in DictUtil._registry.items()
        if du.__module__.startswith("translator_tom.")
    ),
    key=lambda kv: kv[1].__name__,
)
