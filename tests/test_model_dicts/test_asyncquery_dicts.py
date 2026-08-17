"""Tests for the AsyncQuery `*DictUtil` siblings.

Hash parity is covered generically by `test_hash_sweep.py`; these focus on `.new()` and
the `validate=True` path, which requires `TypeAdapter[AsyncQueryDict]` to resolve the
forward-ref fields (`message`/`log_level`) inherited from `QueryDict`.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from translator_tom.model_dicts.asyncquery import (
    AsyncQueryDictUtil,
    AsyncQueryResponseDictUtil,
    AsyncQueryStatusResponseDictUtil,
)


def test_new_includes_callback():
    assert AsyncQueryDictUtil.new("http://cb") == {
        "message": {},
        "callback": "http://cb",
    }


def test_all_adapters_build():
    # regression: inherited QueryDict forward-refs must resolve so the TypeAdapter builds
    for util in (
        AsyncQueryDictUtil,
        AsyncQueryResponseDictUtil,
        AsyncQueryStatusResponseDictUtil,
    ):
        assert util._adapter() is not None


def test_from_json_validate_ok():
    d = AsyncQueryDictUtil.from_json(
        b'{"message": {}, "callback": "http://cb"}', validate=True
    )
    assert d == {"message": {}, "callback": "http://cb"}


def test_from_json_validate_rejects_bad_callback():
    with pytest.raises(ValidationError):
        AsyncQueryDictUtil.from_json(b'{"message": {}, "callback": 123}', validate=True)


def test_response_util_validates():
    d = AsyncQueryResponseDictUtil.from_json(b'{"job_id": "j1"}', validate=True)
    assert d["job_id"] == "j1"
