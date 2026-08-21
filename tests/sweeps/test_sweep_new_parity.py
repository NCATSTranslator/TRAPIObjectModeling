"""Registry-driven `.new()` parity sweep.

Where both a model and its `DictUtil` define `new`, asserts `dictutil.new()` equals
`model.new().to_dict()`. (Hash parity is swept in `test_hash_sweep.py`; structural +
TypedDict-validation parity in `test_sweep_typeddict_parity.py`.) New pairs are covered
automatically.
"""

from __future__ import annotations

import inspect
from typing import Any

import pytest
from _sweep_helpers import sweep_id, DICTUTILS

from translator_tom import TOMBase
from translator_tom.utils.dict_util_base import DictUtil

# Models whose new() is non-deterministic (embeds a now() timestamp), so
# model.new(...).to_dict() can't be compared for equality against the dict form.
# Harness limitation, not a product bug.
NEW_PARITY_SKIP: dict[str, str] = {
    "LogEntry": "new() embeds a now() timestamp; model and dict calls differ each run",
}


def _new_required_params(new_fn: Any) -> list[str]:
    """Names of `new`'s required (no-default) params, excluding the bound cls/self."""
    return [
        p.name
        for p in inspect.signature(new_fn).parameters.values()
        if p.default is inspect.Parameter.empty
        and p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)
    ]


# Pairs where both the model and its DictUtil expose `new`.
_NEW_PAIRS = [
    (model, dictutil)
    for model, dictutil in DICTUTILS
    if hasattr(model, "new") and hasattr(dictutil, "new")
]


@pytest.mark.parametrize(
    ("model", "dictutil"),
    _NEW_PAIRS,
    ids=[sweep_id(du) for _, du in _NEW_PAIRS],
)
def test_new_parity(model: type[TOMBase], dictutil: type[DictUtil[Any]]) -> None:
    reason = NEW_PARITY_SKIP.get(model.__name__)
    if reason is not None:
        pytest.skip(reason)
    # A fixed dummy fills any required arg (e.g. AsyncQuery.new(callback)); the same
    # value goes to both sides so the empty-instance comparison stays valid.
    args = dict.fromkeys(_new_required_params(model.new), "x")
    assert dictutil.new(**args) == model.new(**args).to_dict()
