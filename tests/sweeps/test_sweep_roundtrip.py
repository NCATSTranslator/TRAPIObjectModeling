"""Registry-driven serialization round-trip sweep.

Guards that *every* model survives each I/O pair (dict/json/msgpack) round-trip
and that *every* registered DictUtil round-trips the dict form, using the bare
instances from `_sweep_helpers`. New models/DictUtils are covered automatically.
"""

from __future__ import annotations

from typing import Any

import pytest
from _sweep_helpers import sweep_id, DICTUTILS, MODELS, build

from translator_tom import TOMBase
from translator_tom.utils.dict_util_base import DictUtil

# Models the generic harness can't build-and-revalidate (harness limitation, not a
# product bug): `build` fills fields with type-correct dummies, and a stricter field
# constraint rejects the dummy on the validating (`from_*`) leg of the model
# round-trip. Keyed by class name. This only affects the validating model test; the
# DictUtil round-trip is pure serialization (no validation), so those models run there.
SKIP: dict[str, str] = {
    # LogEntry.timestamp is Field(pattern=ISO-8601); the dummy "x" can't match it.
    "LogEntry": "harness: LogEntry.timestamp requires an ISO-8601 string; dummy 'x' fails the pattern",
    # AsyncQueryStatusResponse has a required logs: list[LogEntry] -> same pattern failure.
    "AsyncQueryStatusResponse": "harness: nested required LogEntry.timestamp requires an ISO-8601 string; dummy 'x' fails the pattern",
}

# Real product bugs: models that genuinely don't round-trip. None found.
XFAIL: dict[str, str] = {}


def _marks(name: str, *, apply_skip: bool) -> list[pytest.MarkDecorator]:
    marks: list[pytest.MarkDecorator] = []
    if apply_skip and name in SKIP:
        marks.append(pytest.mark.skip(reason=SKIP[name]))
    if name in XFAIL:
        marks.append(pytest.mark.xfail(reason=XFAIL[name], strict=False))
    return marks


MODEL_PARAMS = [
    pytest.param(m, marks=_marks(m.__name__, apply_skip=True)) for m in MODELS
]


@pytest.mark.parametrize("model", MODEL_PARAMS, ids=[sweep_id(m) for m in MODELS])
def test_model_roundtrip(model: type[TOMBase]) -> None:
    m = build(model)
    assert type(m).from_dict(m.to_dict()) == m
    assert type(m).from_json(m.to_json()) == m
    assert type(m).from_msgpack(m.to_msgpack()) == m


# DictUtil round-trip does not validate, so the harness SKIPs don't apply here.
DICTUTIL_PARAMS = [
    pytest.param(m, du, marks=_marks(m.__name__, apply_skip=False))
    for m, du in DICTUTILS
]


@pytest.mark.parametrize(
    ("model", "dictutil"),
    DICTUTIL_PARAMS,
    ids=[sweep_id(du) for _, du in DICTUTILS],
)
def test_dictutil_roundtrip(
    model: type[TOMBase], dictutil: type[DictUtil[Any]]
) -> None:
    d = build(model).to_dict()
    # DictUtil to_json/from_json are pure serialization (no validation by default);
    # to_json returns bytes, from_json accepts str | bytes.
    assert dictutil.from_json(dictutil.to_json(d)) == d
    assert dictutil.from_msgpack(dictutil.to_msgpack(d)) == d
