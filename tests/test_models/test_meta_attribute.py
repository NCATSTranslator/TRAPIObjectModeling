"""Tests for translator_tom.models.meta_attribute."""

import pytest
from pydantic import ValidationError

from translator_tom import MetaAttribute


class TestMetaAttributeBasics:
    def test_required_field_only(self):
        m = MetaAttribute(attribute_type_id="biolink:foo")
        assert m.attribute_type_id == "biolink:foo"
        assert m.attribute_source is None
        assert m.original_attribute_names is None
        assert m.constraint_use is False
        assert m.constraint_name is None

    def test_attribute_type_id_required(self):
        with pytest.raises(ValidationError):
            MetaAttribute()  # type: ignore[call-arg]

    def test_original_attribute_names_min_length_enforced(self):
        # Spec requires minItems=1 when present; an empty list must be rejected.
        with pytest.raises(ValidationError):
            MetaAttribute(
                attribute_type_id="biolink:foo", original_attribute_names=[]
            )


class TestOriginalAttributeNamesList:
    def test_returns_empty_when_none(self):
        m = MetaAttribute(attribute_type_id="biolink:foo")
        assert m.original_attribute_names_list == []

    def test_returns_list_when_set(self):
        m = MetaAttribute(
            attribute_type_id="biolink:foo",
            original_attribute_names=["a", "b"],
        )
        assert m.original_attribute_names_list == ["a", "b"]


class TestMetaAttributeHash:
    def test_deterministic(self):
        a = MetaAttribute(
            attribute_type_id="biolink:foo",
            attribute_source="src",
            constraint_use=True,
        )
        b = MetaAttribute(
            attribute_type_id="biolink:foo",
            attribute_source="src",
            constraint_use=True,
        )
        assert a.hash() == b.hash()

    def test_changes_with_type_id(self):
        a = MetaAttribute(attribute_type_id="biolink:foo")
        b = MetaAttribute(attribute_type_id="biolink:bar")
        assert a.hash() != b.hash()

    def test_original_attribute_names_excluded_from_hash(self):
        # hash() ignores original_attribute_names and constraint_name.
        a = MetaAttribute(
            attribute_type_id="biolink:foo", original_attribute_names=["x"]
        )
        b = MetaAttribute(
            attribute_type_id="biolink:foo", original_attribute_names=["y"]
        )
        assert a.hash() == b.hash()


class TestMetaAttributeMergeAttributeLists:
    def test_appends_new_meta_attribute(self):
        a = MetaAttribute(attribute_type_id="biolink:foo")
        b = MetaAttribute(attribute_type_id="biolink:bar")
        old = [a]
        MetaAttribute.merge_attribute_lists(old, [b])
        assert old == [a, b]

    def test_deduplicates_by_hash(self):
        a = MetaAttribute(attribute_type_id="biolink:foo")
        a_dup = MetaAttribute(attribute_type_id="biolink:foo")
        old = [a]
        MetaAttribute.merge_attribute_lists(old, [a_dup])
        assert len(old) == 1
        # New instance wins.
        assert old[0] is a_dup
