"""TypedDict-mirror correctness sweeps: fields match, and to_dict validates.

Two systematic invariants over the model<->TypedDict mirrors (hash parity lives in
`test_hash_sweep.py`, `.new()` parity in `test_sweep_new_parity.py`):

1. Structural parity — each model's serialized field names equal its `{Name}Dict`'s
   resolved keys, so a field added/renamed/removed on one side but not the other fails.
2. Validation — a model's `to_dict()` validates against its DictUtil's `TypedDict`
   adapter, guarding the class of bug where inherited/forward-ref keys can't resolve.

New models/DictUtils are covered automatically.
"""

from __future__ import annotations

import typing
from typing import Any

import pytest
from _sweep_helpers import DICTUTILS, MODELS, build

import translator_tom.model_dicts
from translator_tom import TOMBase
from translator_tom.utils.dict_util_base import DictUtil

# Models with no `{Name}Dict` mirror, each needing an inline justification. Empirically
# empty: every public model currently has a TypedDict mirror. Allow-list a model here only
# for a deliberate omission (e.g. an abstract base with no serialized form) — a REAL missing
# mirror should be fixed in src and reported, not hidden here.
EXPECTED_NO_TYPEDDICT: set[type] = set()

# Intentional, documented model<->TypedDict key differences, keyed by model, with a reason.
# Empirically empty: no model currently diverges from its mirror. A genuine drift should be
# xfail'd and reported instead of allow-listed here.
EXPECTED_KEY_DIFF: dict[type, str] = {}


def _typeddict_for(model: type[TOMBase]) -> Any:
    """The `{Name}Dict` TypedDict mirroring `model`, or None if there is none."""
    return getattr(translator_tom.model_dicts, f"{model.__name__}Dict", None)


def _model_field_keys(model: type[TOMBase]) -> set[str]:
    """Serialized field names of `model` (alias wins, e.g. `negated` -> "not")."""
    return {
        field.serialization_alias or field.alias or name
        for name, field in model.model_fields.items()
    }


def _typeddict_keys(typed_dict: Any) -> set[str]:
    """Resolved keys of a TypedDict, including inherited keys and forward refs."""
    try:
        return set(typing.get_type_hints(typed_dict))
    except Exception:  # fall back to walking the MRO's raw annotations
        keys: set[str] = set()
        for base in getattr(typed_dict, "__mro__", (typed_dict,)):
            keys |= set(getattr(base, "__annotations__", {}))
        return keys


PAIRED = [m for m in MODELS if _typeddict_for(m) is not None]


@pytest.mark.parametrize("model", MODELS, ids=[m.__name__ for m in MODELS])
def test_model_typeddict_accounted_for(model: type[TOMBase]) -> None:
    has_mirror = _typeddict_for(model) is not None
    if model in EXPECTED_NO_TYPEDDICT:
        assert not has_mirror, (
            f"{model.__name__} is allow-listed as having no TypedDict, but "
            f"{model.__name__}Dict now exists — remove it from EXPECTED_NO_TYPEDDICT."
        )
    else:
        assert has_mirror, (
            f"{model.__name__} has no {model.__name__}Dict mirror. Add the TypedDict, "
            f"or (if intentional) allow-list it in EXPECTED_NO_TYPEDDICT with a reason."
        )


@pytest.mark.parametrize("model", PAIRED, ids=[m.__name__ for m in PAIRED])
def test_typeddict_structural_parity(model: type[TOMBase]) -> None:
    if model in EXPECTED_KEY_DIFF:
        pytest.skip(f"documented key diff: {EXPECTED_KEY_DIFF[model]}")
    typed_dict = _typeddict_for(model)
    model_keys = _model_field_keys(model)
    dict_keys = _typeddict_keys(typed_dict)
    missing_from_dict = model_keys - dict_keys
    extra_in_dict = dict_keys - model_keys
    assert model_keys == dict_keys, (
        f"{model.__name__} vs {model.__name__}Dict structural drift: "
        f"missing from dict={sorted(missing_from_dict)}, "
        f"extra in dict={sorted(extra_in_dict)}"
    )


# Real DictUtil TypedDict-resolution bugs get an xfail entry here (currently none).
TO_DICT_VALIDATE_XFAIL: dict[str, str] = {}


@pytest.mark.parametrize(
    ("model", "dictutil"),
    DICTUTILS,
    ids=[du.__name__ for _, du in DICTUTILS],
)
def test_to_dict_validates_typeddict(
    model: type[TOMBase], dictutil: type[DictUtil[Any]]
) -> None:
    """A model's `to_dict()` validates against its DictUtil's (possibly inherited) TypedDict."""
    reason = TO_DICT_VALIDATE_XFAIL.get(dictutil.__name__)
    if reason is not None:
        pytest.xfail(reason)
    adapter = dictutil._adapter()  # must resolve the (possibly inherited) TypedDict
    adapter.validate_python(build(model).to_dict())  # must not raise
