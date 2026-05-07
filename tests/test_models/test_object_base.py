"""Tests for translator_tom.utils.object_base."""

from typing import ClassVar

import pytest
from pydantic import ConfigDict

from translator_tom import Attribute, RetrievalSource
from translator_tom.utils.object_base import TOMBase, _stable_repr


class _AllowExtra(TOMBase):
    """Simple TOMBase subclass with the default extra='allow' config."""

    name: str = "default"
    value: int = 0


class _IgnoreExtra(TOMBase):
    """TOMBase subclass that disallows extras (sets __pydantic_extra__ to None)."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        defer_build=False,
        validate_assignment=False,
        revalidate_instances="never",
        validate_default=False,
        protected_namespaces=(),
        extra="ignore",
    )

    name: str = "default"


class TestStableRepr:
    """Direct tests for the _stable_repr helper used by hash()."""

    def test_passes_through_primitives(self):
        assert _stable_repr(42) == 42
        assert _stable_repr("foo") == "foo"
        assert _stable_repr(None) is None

    def test_dict_is_recursive(self):
        attr = Attribute(attribute_type_id="biolink:foo", value=1)
        out = _stable_repr({"k": attr})
        assert out == {"k": attr.hash()}

    def test_list_is_recursive(self):
        attr = Attribute(attribute_type_id="biolink:foo", value=1)
        out = _stable_repr([attr, 1])
        assert out == [attr.hash(), 1]

    def test_tuple_is_recursive(self):
        attr = Attribute(attribute_type_id="biolink:foo", value=1)
        out = _stable_repr((attr, 2))
        assert out == (attr.hash(), 2)
        assert isinstance(out, tuple)

    def test_set_becomes_frozenset(self):
        out = _stable_repr({1, 2, 3})
        assert out == frozenset({1, 2, 3})
        assert isinstance(out, frozenset)

    def test_frozenset_stays_frozenset(self):
        out = _stable_repr(frozenset({1, 2}))
        assert out == frozenset({1, 2})
        assert isinstance(out, frozenset)

    def test_tombase_replaced_by_hash(self):
        attr = Attribute(attribute_type_id="biolink:foo", value=1)
        assert _stable_repr(attr) == attr.hash()


class TestDictRoundTrip:
    def test_round_trip(self):
        original = Attribute(attribute_type_id="biolink:foo", value=1)
        restored = Attribute.from_dict(original.to_dict())
        assert restored == original

    def test_to_dict_returns_json_compatible(self):
        attr = Attribute(attribute_type_id="biolink:foo", value=1)
        # `mode="json"` produces only JSON-compatible primitives.
        as_dict = attr.to_dict()
        assert as_dict["attribute_type_id"] == "biolink:foo"
        assert as_dict["value"] == 1


class TestJsonRoundTrip:
    def test_round_trip_from_bytes(self):
        original = Attribute(attribute_type_id="biolink:foo", value=1)
        restored = Attribute.from_json(original.to_json())
        assert restored == original

    def test_to_json_default_returns_bytes(self):
        attr = Attribute(attribute_type_id="biolink:foo", value=1)
        out = attr.to_json()
        assert isinstance(out, bytes)

    def test_to_json_as_str_true_returns_str(self):
        attr = Attribute(attribute_type_id="biolink:foo", value=1)
        out = attr.to_json(as_str=True)
        assert isinstance(out, str)
        assert "biolink:foo" in out

    def test_to_json_as_str_false_returns_bytes(self):
        attr = Attribute(attribute_type_id="biolink:foo", value=1)
        out = attr.to_json(as_str=False)
        assert isinstance(out, bytes)

    def test_round_trip_from_str(self):
        original = Attribute(attribute_type_id="biolink:foo", value=1)
        restored = Attribute.from_json(original.to_json(as_str=True))
        assert restored == original


class TestMsgpackRoundTrip:
    def test_round_trip(self):
        original = Attribute(attribute_type_id="biolink:foo", value=1)
        restored = Attribute.from_msgpack(original.to_msgpack())
        assert restored == original

    def test_to_msgpack_returns_bytes(self):
        attr = Attribute(attribute_type_id="biolink:foo", value=1)
        assert isinstance(attr.to_msgpack(), bytes)


class TestHashAndEquality:
    def test_hash_is_deterministic(self):
        a = Attribute(attribute_type_id="biolink:foo", value=1)
        b = Attribute(attribute_type_id="biolink:foo", value=1)
        assert a.hash() == b.hash()

    def test_hash_changes_with_field(self):
        a = Attribute(attribute_type_id="biolink:foo", value=1)
        b = Attribute(attribute_type_id="biolink:foo", value=2)
        assert a.hash() != b.hash()

    def test_dunder_hash_is_int(self):
        a = Attribute(attribute_type_id="biolink:foo", value=1)
        assert isinstance(hash(a), int)

    def test_equal_objects_share_dunder_hash(self):
        a = Attribute(attribute_type_id="biolink:foo", value=1)
        b = Attribute(attribute_type_id="biolink:foo", value=1)
        assert hash(a) == hash(b)

    def test_eq_returns_true_for_same_fields(self):
        a = Attribute(attribute_type_id="biolink:foo", value=1)
        b = Attribute(attribute_type_id="biolink:foo", value=1)
        assert a == b

    def test_eq_returns_false_for_different_fields(self):
        a = Attribute(attribute_type_id="biolink:foo", value=1)
        b = Attribute(attribute_type_id="biolink:foo", value=2)
        assert a != b

    def test_eq_returns_false_for_different_types(self):
        attr = Attribute(attribute_type_id="biolink:foo", value=1)
        src = RetrievalSource(
            resource_id="infores:foo",
            resource_role="primary_knowledge_source",
        )
        assert attr != src

    def test_eq_returns_false_for_non_tombase(self):
        attr = Attribute(attribute_type_id="biolink:foo", value=1)
        assert attr != "not a TOMBase"
        assert attr != 42

    def test_extras_not_included_in_hash(self):
        # TOMBase.hash() iterates only declared fields, ignoring extras.
        a = _AllowExtra(name="x", extra_field="one")  # type: ignore[call-arg]
        b = _AllowExtra(name="x", extra_field="two")  # type: ignore[call-arg]
        assert a.hash() == b.hash()


class TestExtraDict:
    def test_returns_extras_when_allowed(self):
        m = _AllowExtra(name="x", foo="bar", baz=1)  # type: ignore[call-arg]
        assert m.extra_dict == {"foo": "bar", "baz": 1}

    def test_returns_empty_dict_when_not_allowed(self):
        m = _IgnoreExtra(name="x")
        # __pydantic_extra__ is None for extra='ignore', so extra_dict yields {}
        assert m.extra_dict == {}

    def test_returns_empty_dict_when_no_extras_passed(self):
        m = _AllowExtra(name="x")
        assert m.extra_dict == {}


class TestExtraGet:
    def test_returns_value_when_present(self):
        m = _AllowExtra(name="x", foo="bar")  # type: ignore[call-arg]
        assert m.extra_get("foo") == "bar"

    def test_returns_default_when_absent(self):
        m = _AllowExtra(name="x")
        assert m.extra_get("missing", "fallback") == "fallback"

    def test_returns_none_default(self):
        m = _AllowExtra(name="x")
        assert m.extra_get("missing") is None

    def test_raises_when_extras_disallowed(self):
        m = _IgnoreExtra(name="x")
        with pytest.raises(ValueError, match="does not allow extra values"):
            m.extra_get("anything")


class TestExtraSet:
    def test_does_not_raise_when_extras_allowed(self):
        m = _AllowExtra(name="x")
        m.extra_set("foo", "bar")  # should not raise

    def test_raises_when_extras_disallowed(self):
        m = _IgnoreExtra(name="x")
        with pytest.raises(ValueError, match="does not allow extra values"):
            m.extra_set("foo", "bar")
