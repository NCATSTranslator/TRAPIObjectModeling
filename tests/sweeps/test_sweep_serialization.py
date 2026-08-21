"""Serialization sweep: optional ``None`` fields must never leak into serialized output.

``to_dict()``/``to_json()`` serialize with ``exclude_none=True`` (see
``translator_tom.utils.object_base``), so any optional field left as ``None`` (the
"None over empty-list" convention the whole dict layer depends on) must be *absent*
from the output rather than emitted as ``null``. The bare instances from
``_sweep_helpers.build()`` fill only required fields, leaving every optional field
``None``, so this holds every optional-``None`` field to the invariant automatically.
"""

from __future__ import annotations

import orjson
import pytest
from _sweep_helpers import sweep_id, MODELS, build
from pydantic.fields import FieldInfo

from translator_tom import TOMBase


def _none_optional_fields(model: type[TOMBase]) -> dict[str, FieldInfo]:
    """Optional fields whose default is ``None`` (those subject to the exclude_none invariant).

    Fields with a non-``None`` default (e.g. ``bypass_cache: bool = False``) are excluded:
    ``exclude_none`` only drops ``None``, so they carry no obligation here.
    """
    return {
        name: field
        for name, field in model.model_fields.items()
        if not field.is_required() and field.default is None
    }


def _serialized_key(name: str, field: FieldInfo) -> str:
    """The key a field serializes under, honoring an alias if one is set (e.g. ``negated`` -> ``not``)."""
    return field.serialization_alias or field.alias or name


@pytest.mark.parametrize("model", MODELS, ids=[sweep_id(m) for m in MODELS])
def test_no_none_values_leak(model: type[TOMBase]) -> None:
    """A bare instance serializes with no top-level ``None`` value (all optionals dropped)."""
    output = build(model).to_dict()
    assert all(v is not None for v in output.values()), (
        f"{model.__name__}.to_dict() emitted top-level None value(s): "
        f"{[k for k, v in output.items() if v is None]}"
    )


@pytest.mark.parametrize("model", MODELS, ids=[sweep_id(m) for m in MODELS])
def test_none_optional_fields_absent(model: type[TOMBase]) -> None:
    """Every optional-``None`` field's key is absent from both ``to_dict()`` and ``to_json()``."""
    inst = build(model)
    as_dict = inst.to_dict()
    as_json = orjson.loads(inst.to_json())
    for name, field in _none_optional_fields(model).items():
        key = _serialized_key(name, field)
        assert key not in as_dict, (
            f"{model.__name__}.{name} (key {key!r}) leaked into to_dict() while None"
        )
        assert key not in as_json, (
            f"{model.__name__}.{name} (key {key!r}) leaked into to_json() while None"
        )


@pytest.mark.parametrize("model", MODELS, ids=[sweep_id(m) for m in MODELS])
def test_explicit_none_excluded(model: type[TOMBase]) -> None:
    """Explicitly assigning ``None`` (models are mutable) still yields an absent key."""
    inst = build(model)
    fields = _none_optional_fields(model)
    for name in fields:
        setattr(inst, name, None)
    as_dict = inst.to_dict()
    as_json = orjson.loads(inst.to_json())
    for name, field in fields.items():
        key = _serialized_key(name, field)
        assert key not in as_dict, (
            f"{model.__name__}.{name} (key {key!r}) serialized despite being explicitly None"
        )
        assert key not in as_json, (
            f"{model.__name__}.{name} (key {key!r}) serialized to json despite being explicitly None"
        )
