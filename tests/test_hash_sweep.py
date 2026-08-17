"""Registry-driven hash smoketest + model<->DictUtil hash parity sweep.

Guards that *every* model hashes without crashing and that *every* registered
DictUtil's hash matches its model's, using the bare instances from `_sweep_helpers`.
New models/DictUtils are covered automatically.
"""

from __future__ import annotations

from typing import Any

import pytest
from _sweep_helpers import DICTUTILS, MODELS, build

from translator_tom import TOMBase
from translator_tom.utils.dict_util_base import DictUtil


@pytest.mark.parametrize("model", MODELS, ids=[m.__name__ for m in MODELS])
def test_model_hash_smoke(model: type[TOMBase]) -> None:
    result = build(model).hash()
    assert isinstance(result, str) and result


@pytest.mark.parametrize(
    ("model", "dictutil"),
    DICTUTILS,
    ids=[du.__name__ for _, du in DICTUTILS],
)
def test_dictutil_hash_parity(
    model: type[TOMBase], dictutil: type[DictUtil[Any]]
) -> None:
    inst = build(model)
    assert dictutil.hash(inst.to_dict()) == inst.hash()
