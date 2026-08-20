"""Tests for the `*DictUtil` classes in `model_dicts/meta_attribute.py` and
`model_dicts/meta_qualifier.py`, asserting parity with their Pydantic models.
"""

from __future__ import annotations

import pytest

from translator_tom.v1_6.model_dicts.meta_attribute import (
    MetaAttributeDict,
    MetaAttributeDictUtil,
)
from translator_tom.v1_6.model_dicts.meta_qualifier import (
    MetaQualifierDict,
    MetaQualifierDictUtil,
)
from translator_tom.v1_6.models.meta_attribute import MetaAttribute
from translator_tom.v1_6.models.meta_qualifier import MetaQualifier

# ============================================================================
# MetaAttributeDictUtil
# ============================================================================


class TestMetaAttributeListAccessor:
    def test_missing_returns_empty(self):
        attr: MetaAttributeDict = {"attribute_type_id": "biolink:foo"}
        assert MetaAttributeDictUtil.original_attribute_names_list(attr) == []

    def test_none_returns_empty(self):
        attr: MetaAttributeDict = {
            "attribute_type_id": "biolink:foo",
            "original_attribute_names": None,
        }
        assert MetaAttributeDictUtil.original_attribute_names_list(attr) == []

    def test_populated(self):
        attr: MetaAttributeDict = {
            "attribute_type_id": "biolink:foo",
            "original_attribute_names": ["col_a", "col_b"],
        }
        assert MetaAttributeDictUtil.original_attribute_names_list(attr) == [
            "col_a",
            "col_b",
        ]


class TestMetaAttributeHashParity:
    @pytest.mark.parametrize("constraint_use", [True, False])
    def test_constraint_use_states(self, constraint_use: bool):
        m = MetaAttribute(
            attribute_type_id="biolink:foo",
            attribute_source="infores:x",
            constraint_use=constraint_use,
        )
        assert MetaAttributeDictUtil.hash(m.to_dict()) == m.hash()

    def test_minimal(self):
        m = MetaAttribute(attribute_type_id="biolink:foo")
        assert MetaAttributeDictUtil.hash(m.to_dict()) == m.hash()

    def test_hash_ignores_non_identity_fields(self):
        # Only attribute_type_id/source/constraint_use feed the hash.
        a = MetaAttribute(
            attribute_type_id="biolink:foo", original_attribute_names=["x"]
        )
        b = MetaAttribute(
            attribute_type_id="biolink:foo", original_attribute_names=["y"]
        )
        assert MetaAttributeDictUtil.hash(a.to_dict()) == MetaAttributeDictUtil.hash(
            b.to_dict()
        )


class TestMetaAttributeMerge:
    def _assert_parity(
        self, old: list[MetaAttribute], new: list[MetaAttribute]
    ) -> None:
        old_dicts = [m.to_dict() for m in old]
        new_dicts = [m.to_dict() for m in new]
        MetaAttribute.merge_attribute_lists(old, new)
        MetaAttributeDictUtil.merge_attribute_lists(old_dicts, new_dicts)
        assert old_dicts == [m.to_dict() for m in old]

    def test_union_with_overlap(self):
        self._assert_parity(
            [
                MetaAttribute(attribute_type_id="biolink:a", constraint_use=True),
                MetaAttribute(attribute_type_id="biolink:b"),
            ],
            [
                MetaAttribute(attribute_type_id="biolink:b"),
                MetaAttribute(attribute_type_id="biolink:c"),
            ],
        )


# ============================================================================
# MetaQualifierDictUtil
# ============================================================================


class TestMetaQualifierListAccessor:
    def test_missing_returns_empty(self):
        mq: MetaQualifierDict = {"qualifier_type_id": "biolink:subject_aspect_qualifier"}
        assert MetaQualifierDictUtil.applicable_values_list(mq) == []

    def test_none_returns_empty(self):
        mq: MetaQualifierDict = {
            "qualifier_type_id": "biolink:subject_aspect_qualifier",
            "applicable_values": None,
        }
        assert MetaQualifierDictUtil.applicable_values_list(mq) == []

    def test_populated(self):
        mq: MetaQualifierDict = {
            "qualifier_type_id": "biolink:subject_aspect_qualifier",
            "applicable_values": ["activity", "abundance"],
        }
        assert MetaQualifierDictUtil.applicable_values_list(mq) == [
            "activity",
            "abundance",
        ]

    def test_parity_with_model(self):
        m = MetaQualifier(
            qualifier_type_id="biolink:subject_aspect_qualifier",
            applicable_values=["activity"],
        )
        assert (
            MetaQualifierDictUtil.applicable_values_list(m.to_dict())
            == m.applicable_values_list
        )
