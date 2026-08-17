"""Registry-driven sweep of the None-safe `*_list`/`*_dict` convenience accessors.

Two cross-cutting invariants, over the bare instances from `_sweep_helpers`:

1. Every model `X_list`/`X_dict` property is None-safe: with its backing field set
   to `None`, it returns `[]`/`{}` rather than raising or yielding `None`.
2. Each such accessor is mirrored by a same-named, callable static accessor on the
   model's `DictUtil`, empty-safe on both `{}` and `{X: None}`.

New models/accessors are covered automatically. `extra_dict` (defined on `TOMBase`
over pydantic's extras bucket, not a declared field) is out of scope for both.
"""

from __future__ import annotations

import inspect

import pytest
from _sweep_helpers import DICTUTILS, MODELS, build

from translator_tom import TOMBase

_DU_BY_MODEL = dict(DICTUTILS)


def _property_accessors(model: type[TOMBase]) -> list[str]:
    """Names of `*_list`/`*_dict` `property` accessors visible on `model`."""
    return sorted(
        name
        for name in dir(model)
        if (name.endswith("_list") or name.endswith("_dict"))
        and isinstance(inspect.getattr_static(model, name, None), property)
    )


# Flat (model, accessor) sweep, so ids read as e.g. "Response.workflow_list".
_ACCESSORS = [(model, name) for model in MODELS for name in _property_accessors(model)]
_ACCESSOR_IDS = [f"{m.__name__}.{n}" for m, n in _ACCESSORS]


@pytest.mark.parametrize(("model", "accessor"), _ACCESSORS, ids=_ACCESSOR_IDS)
def test_model_accessor_none_safe(model: type[TOMBase], accessor: str) -> None:
    """`X_list`/`X_dict` returns the empty container when its backing field is `None`."""
    field = accessor[:-5]  # strip "_list"/"_dict" -> backing field name
    if field not in model.model_fields:
        pytest.skip(
            f"{accessor}: backing field {field!r} is not a declared model field "
            "(extras accessor); field-None-safety N/A"
        )
    instance = build(model)
    setattr(instance, field, None)  # models are mutable; validate_assignment is off
    result = getattr(instance, accessor)
    assert result == ([] if accessor.endswith("_list") else {})


def _parity_param(model: type[TOMBase], accessor: str) -> pytest.ParameterSet:
    """Build the parity param, xfail-marking a real-field accessor with no dict mirror."""
    field = accessor[:-5]
    marks: pytest.MarkDecorator | tuple[()] = ()
    if field in model.model_fields:
        dictutil = _DU_BY_MODEL.get(model)
        mirror = getattr(dictutil, accessor, None) if dictutil is not None else None
        if not callable(mirror):
            du_name = dictutil.__name__ if dictutil is not None else "(no DictUtil)"
            marks = pytest.mark.xfail(
                reason=(
                    f"BUG: {model.__name__}.{accessor} has no same-named mirror on "
                    f"{du_name}; DictUtil parity gap"
                ),
                strict=False,
            )
    return pytest.param(model, accessor, marks=marks, id=f"{model.__name__}.{accessor}")


_PARITY_PARAMS = [_parity_param(m, n) for m, n in _ACCESSORS]


@pytest.mark.parametrize(("model", "accessor"), _PARITY_PARAMS)
def test_dictutil_accessor_parity(model: type[TOMBase], accessor: str) -> None:
    """The model's `DictUtil` mirrors `X_list`/`X_dict`, empty-safe on `{}` and `{X: None}`."""
    field = accessor[:-5]
    if field not in model.model_fields:
        pytest.skip(
            f"{accessor}: extras accessor; no DictUtil mirror expected (intentional)"
        )
    dictutil = _DU_BY_MODEL.get(model)
    assert dictutil is not None, f"no DictUtil registered for {model.__name__}"
    mirror = getattr(dictutil, accessor, None)
    assert callable(mirror), f"{dictutil.__name__} is missing accessor {accessor!r}"
    empty = [] if accessor.endswith("_list") else {}
    assert mirror({}) == empty
    assert mirror({field: None}) == empty
