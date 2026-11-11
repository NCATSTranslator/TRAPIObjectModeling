"""Tests for the I/O + validation methods on the `DictUtil` base.

`from_json`/`from_msgpack`/`from_dict` optionally validate the parsed dict against the
util's `TypedDict` — recursively, and without building model instances — via a cached
`TypeAdapter`. With `validate=True` the coerced dict is returned: unknown keys are
kept where the mirrored model allows extras (`TOMBaseDict`) and rejected where it
forbids them (`TOMBaseDictForbid`), mirroring the model layer.
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
from translator_tom.v2_0.model_dicts.log_entry import LogEntryDictUtil
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

    def test_from_dict_passes_garbage_through(self):
        assert AttributeDictUtil.from_dict({"not_a_field": 5}) == {"not_a_field": 5}

    def test_from_dict_returns_same_object_uncopied(self):
        # Without validation from_dict is a pure cast: the original dict is returned as-is.
        original = {"attribute_type_id": "biolink:foo", "value": 1}
        assert AttributeDictUtil.from_dict(original) is original


# ============================================================================
# from_json(validate=True)
# ============================================================================


class TestFromJsonValidate:
    def test_valid_passes(self):
        attr: AttributeDict = {"attribute_type_id": "biolink:foo", "value": 1}
        assert (
            AttributeDictUtil.from_json(orjson.dumps(attr), validate=True) == attr
        )

    def test_allow_type_preserves_extras(self):
        # LogEntry allows extras (TOMBaseDict); validation keeps the unknown key.
        entry = {"timestamp": "2024-01-01T00:00:00Z", "message": "hi", "surprise": "kept"}
        out = LogEntryDictUtil.from_json(orjson.dumps(entry), validate=True)
        assert out == entry

    def test_forbid_type_rejects_extras(self):
        # Attribute forbids extras (TOMBaseDictForbid), matching the model.
        attr = {"attribute_type_id": "biolink:foo", "value": 1, "surprise": "no"}
        with pytest.raises(ValidationError):
            AttributeDictUtil.from_json(orjson.dumps(attr), validate=True)

    def test_coerces_scalar(self):
        # validate=True returns the TypeAdapter's coerced output, not the raw parse.
        constraint = {"id": "biolink:x", "operator": "==", "value": 1, "not": "true"}
        out = AttributeConstraintDictUtil.from_json(
            orjson.dumps(constraint), validate=True
        )
        assert out["not"] is True

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
        entry = {"timestamp": "2024-01-01T00:00:00Z", "message": "hi", "surprise": "kept"}
        out = LogEntryDictUtil.from_msgpack(ormsgpack.packb(entry), validate=True)
        assert out == entry

    def test_invalid_raises(self):
        with pytest.raises(ValidationError):
            AttributeDictUtil.from_msgpack(ormsgpack.packb({"value": 1}), validate=True)


# ============================================================================
# from_dict(validate=True) — mirrors from_json, but over an in-memory dict
# ============================================================================


class TestFromDictValidate:
    def test_valid_passes(self):
        attr: AttributeDict = {"attribute_type_id": "biolink:foo", "value": 1}
        assert AttributeDictUtil.from_dict(attr, validate=True) == attr

    def test_returns_new_object_when_validated(self):
        # validate=True returns the TypeAdapter's output, not the input dict.
        original = {"attribute_type_id": "biolink:foo", "value": 1}
        assert AttributeDictUtil.from_dict(original, validate=True) is not original

    def test_allow_type_preserves_extras(self):
        # LogEntry allows extras (TOMBaseDict); validation keeps the unknown key.
        entry = {"timestamp": "2024-01-01T00:00:00Z", "message": "hi", "surprise": "kept"}
        out = LogEntryDictUtil.from_dict(entry, validate=True)
        assert out == entry

    def test_forbid_type_rejects_extras(self):
        # Attribute forbids extras (TOMBaseDictForbid), matching the model.
        attr = {"attribute_type_id": "biolink:foo", "value": 1, "surprise": "no"}
        with pytest.raises(ValidationError):
            AttributeDictUtil.from_dict(attr, validate=True)

    def test_coerces_scalar(self):
        # validate=True (lax) coerces like the TypeAdapter: "true" -> True.
        constraint = {"id": "biolink:x", "operator": "==", "value": 1, "not": "true"}
        out = AttributeConstraintDictUtil.from_dict(constraint, validate=True)
        assert out["not"] is True

    def test_strict_rejects_coercion(self):
        # strict=True disallows the lax "true" -> bool coercion above.
        constraint = {"id": "biolink:x", "operator": "==", "value": 1, "not": "true"}
        with pytest.raises(ValidationError):
            AttributeConstraintDictUtil.from_dict(constraint, validate=True, strict=True)

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            AttributeDictUtil.from_dict({"value": 1}, validate=True)

    def test_wrong_scalar_type_raises(self):
        # attribute_type_id is a CURIE (str); an int is rejected even in lax mode.
        bad = {"attribute_type_id": 123, "value": 1}
        with pytest.raises(ValidationError):
            AttributeDictUtil.from_dict(bad, validate=True)

    def test_recursive_nested_valid_passes(self):
        good = {
            "attribute_type_id": "biolink:foo",
            "value": 1,
            "attributes": [{"attribute_type_id": "biolink:bar", "value": 2}],
        }
        assert AttributeDictUtil.from_dict(good, validate=True) == good

    def test_recursive_nested_invalid_raises(self):
        # Outer object is fine; the nested sub-attribute is missing its required key.
        bad = {
            "attribute_type_id": "biolink:foo",
            "value": 1,
            "attributes": [{"value": 2}],
        }
        with pytest.raises(ValidationError):
            AttributeDictUtil.from_dict(bad, validate=True)

    def test_model_round_trip_parity(self):
        # A real model's dict form validates and yields exactly that dict form.
        a = Attribute(
            attribute_type_id="biolink:foo",
            value=[1, 2],
            attributes=[Attribute(attribute_type_id="biolink:bar", value=3)],
        )
        assert AttributeDictUtil.from_dict(a.to_dict(), validate=True) == a.to_dict()


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
