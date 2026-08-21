"""Tests for the I/O + validation methods on the `DictUtil` base.

`from_json`/`from_msgpack` optionally validate the parsed dict against the util's
`TypedDict` — recursively, and without building model instances — via a cached
`TypeAdapter`. The *parsed* dict is returned unchanged, so extra keys and original
values survive even when validation runs.
"""

from __future__ import annotations

import orjson
import ormsgpack
import pytest
from pydantic import TypeAdapter, ValidationError

from translator_tom.v2_0.model_dicts.attribute import (
    AttributeConstraintDictUtil,
    AttributeDict,
    AttributeDictUtil,
)
from translator_tom.v2_0.models.attribute import Attribute

# ============================================================================
# Default behavior — no validation unless asked
# ============================================================================


class TestNoValidation:
    def test_from_json_passes_garbage_through(self):
        assert AttributeDictUtil.from_json(b'{"not_a_field": 5}') == {"not_a_field": 5}

    def test_from_msgpack_passes_garbage_through(self):
        packed = ormsgpack.packb({"not_a_field": 5})
        assert AttributeDictUtil.from_msgpack(packed) == {"not_a_field": 5}


# ============================================================================
# from_json(validate=True)
# ============================================================================


class TestFromJsonValidate:
    def test_valid_passes(self):
        attr: AttributeDict = {"attribute_type_id": "biolink:foo", "value": 1}
        assert (
            AttributeDictUtil.from_json(orjson.dumps(attr), validate=True) == attr
        )

    def test_returns_loaded_dict_preserving_extras(self):
        # The validator drops keys not in the TypedDict; from_json must still return
        # them, since it returns the parsed dict, not the validator's output.
        attr = {"attribute_type_id": "biolink:foo", "value": 1, "surprise": "kept"}
        out = AttributeDictUtil.from_json(orjson.dumps(attr), validate=True)
        # Equality proves the unknown key survived; a dropped key would fail this.
        assert out == attr

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            AttributeDictUtil.from_json(orjson.dumps({"value": 1}), validate=True)

    def test_wrong_scalar_type_raises(self):
        # attribute_type_id is a CURIE (str); an int is rejected even in lax mode.
        bad = {"attribute_type_id": 123, "value": 1}
        with pytest.raises(ValidationError):
            AttributeDictUtil.from_json(orjson.dumps(bad), validate=True)

    def test_recursive_nested_valid_passes(self):
        good = {
            "attribute_type_id": "biolink:foo",
            "value": 1,
            "attributes": [{"attribute_type_id": "biolink:bar", "value": 2}],
        }
        assert AttributeDictUtil.from_json(orjson.dumps(good), validate=True) == good

    def test_recursive_nested_invalid_raises(self):
        # Outer object is fine; the nested sub-attribute is missing its required key.
        bad = {
            "attribute_type_id": "biolink:foo",
            "value": 1,
            "attributes": [{"value": 2}],
        }
        with pytest.raises(ValidationError):
            AttributeDictUtil.from_json(orjson.dumps(bad), validate=True)

    def test_model_json_round_trip_parity(self):
        # A real model's JSON validates and yields exactly the model's dict form.
        a = Attribute(
            attribute_type_id="biolink:foo",
            value=[1, 2],
            attributes=[Attribute(attribute_type_id="biolink:bar", value=3)],
        )
        assert AttributeDictUtil.from_json(a.to_json(), validate=True) == a.to_dict()


# ============================================================================
# from_msgpack(validate=True) — mirrors from_json
# ============================================================================


class TestFromMsgpackValidate:
    def test_valid_passes_preserving_extras(self):
        attr = {"attribute_type_id": "biolink:foo", "value": 1, "surprise": "kept"}
        out = AttributeDictUtil.from_msgpack(ormsgpack.packb(attr), validate=True)
        assert out == attr

    def test_invalid_raises(self):
        with pytest.raises(ValidationError):
            AttributeDictUtil.from_msgpack(ormsgpack.packb({"value": 1}), validate=True)


# ============================================================================
# TypeAdapter caching
# ============================================================================


class TestAdapterCaching:
    def test_same_instance_across_calls(self):
        assert AttributeDictUtil._adapter() is AttributeDictUtil._adapter()

    def test_distinct_per_subclass(self):
        assert AttributeDictUtil._adapter() is not AttributeConstraintDictUtil._adapter()

    def test_adapter_is_a_type_adapter(self):
        assert isinstance(AttributeDictUtil._adapter(), TypeAdapter)
