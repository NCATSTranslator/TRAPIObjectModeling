"""Registry-driven hash smoketest + model<->DictUtil parity sweep.

Guards that *every* model hashes without crashing and that *every* registered
DictUtil's hash matches its model's, using bare minimal instances built generically
from the field annotations. New models/DictUtils are covered automatically.

This is deliberately a smoketest: instances are bare (required scalars get dummy
values, required lists one element, dicts/sets empty), so it does not exercise
deeply-nested container hashing — the per-model tests cover realistic content.
"""

from __future__ import annotations

import enum
import types
from typing import Any, Literal, Union, get_args, get_origin

import pytest

import translator_tom
import translator_tom.model_dicts  # noqa: F401  (import populates the DictUtil registry)
from translator_tom import TOMBase
from translator_tom.utils.dict_util_base import DictUtil


def _unwrap(ann: Any) -> Any:
    while hasattr(ann, "__metadata__"):  # Annotated[X, ...] -> X
        ann = ann.__origin__
    return ann


def _dummy(ann: Any) -> Any:
    """Return a minimal, type-correct value for a field annotation (validation skipped)."""
    ann = _unwrap(ann)
    origin = get_origin(ann)
    if origin is Union or origin is types.UnionType:
        members = [a for a in get_args(ann) if a is not type(None)]
        return _dummy(members[0]) if members else None
    if origin is list:  # one element, to satisfy min_length lists (e.g. Edge.sources)
        elems = get_args(ann)
        return [_dummy(elems[0])] if elems else []
    if origin in (set, frozenset, tuple):
        return []
    if origin is dict:
        return {}
    if origin is Literal:
        return get_args(ann)[0]
    if isinstance(ann, type):
        if issubclass(ann, TOMBase):
            return _build(ann)
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


def _build(model: type[TOMBase]) -> TOMBase:
    """A bare, unvalidated instance with only required fields filled by `_dummy`."""
    values = {
        name: _dummy(field.annotation)
        for name, field in model.model_fields.items()
        if field.is_required()
    }
    return model.model_construct(**values)


_MODELS = sorted(
    {
        obj
        for name in translator_tom.__all__
        if isinstance((obj := getattr(translator_tom, name)), type)
        and issubclass(obj, TOMBase)
        and obj is not TOMBase
    },
    key=lambda c: c.__name__,
)
_DICTUTILS = sorted(DictUtil._registry.items(), key=lambda kv: kv[1].__name__)


@pytest.mark.parametrize("model", _MODELS, ids=[m.__name__ for m in _MODELS])
def test_model_hash_smoke(model: type[TOMBase]) -> None:
    result = _build(model).hash()
    assert isinstance(result, str) and result


@pytest.mark.parametrize(
    ("model", "dictutil"),
    _DICTUTILS,
    ids=[du.__name__ for _, du in _DICTUTILS],
)
def test_dictutil_hash_parity(
    model: type[TOMBase], dictutil: type[DictUtil[Any]]
) -> None:
    inst = _build(model)
    assert dictutil.hash(inst.to_dict()) == inst.hash()
