"""Tests for the `*DictUtil` sibling classes in `model_dicts/attribute.py`.

The util classes reimplement the utility methods of the `Attribute` and
`AttributeConstraint` Pydantic models for their `TypedDict` equivalents. Tests
assert parity by comparing dict-util results against the models operating on the
same data.
"""

from __future__ import annotations

import pytest

from translator_tom.v1_6.model_dicts.attribute import (
    AttributeConstraintDictUtil,
    AttributeDict,
    AttributeDictUtil,
)
from translator_tom.v1_6.models.attribute import Attribute, AttributeConstraint
from translator_tom.v1_6.models.meta_attribute import MetaAttribute

# ============================================================================
# AttributeDictUtil.attributes_list
# ============================================================================


class TestAttributeDictUtilListAccessor:
    def test_missing_key_returns_empty(self):
        attr: AttributeDict = {"attribute_type_id": "biolink:foo", "value": 1}
        assert AttributeDictUtil.attributes_list(attr) == []

    def test_explicit_none_returns_empty(self):
        attr: AttributeDict = {
            "attribute_type_id": "biolink:foo",
            "value": 1,
            "attributes": None,
        }
        assert AttributeDictUtil.attributes_list(attr) == []

    def test_populated_returns_value(self):
        sub: AttributeDict = {"attribute_type_id": "biolink:bar", "value": 2}
        attr: AttributeDict = {
            "attribute_type_id": "biolink:foo",
            "value": 1,
            "attributes": [sub],
        }
        assert AttributeDictUtil.attributes_list(attr) == [sub]


# ============================================================================
# AttributeDictUtil.hash — parity with Attribute.hash (incl. nested recursion)
# ============================================================================


class TestAttributeHashParity:
    def test_scalar_only(self):
        a = Attribute(attribute_type_id="biolink:foo", value=1)
        assert AttributeDictUtil.hash(a.to_dict()) == a.hash()

    def test_all_scalar_fields(self):
        a = Attribute(
            attribute_type_id="biolink:foo",
            original_attribute_name="foo",
            value=[1, 2, 3],
            value_type_id="biolink:bar",
            attribute_source="infores:x",
            value_url="http://example.com",
            description="d",
        )
        assert AttributeDictUtil.hash(a.to_dict()) == a.hash()

    def test_nested_attributes(self):
        sub = Attribute(attribute_type_id="biolink:sub", value="x")
        a = Attribute(attribute_type_id="biolink:foo", value=1, attributes=[sub])
        assert AttributeDictUtil.hash(a.to_dict()) == a.hash()

    def test_deeply_nested_attributes(self):
        leaf = Attribute(attribute_type_id="biolink:leaf", value=3)
        mid = Attribute(attribute_type_id="biolink:mid", value=2, attributes=[leaf])
        a = Attribute(attribute_type_id="biolink:foo", value=1, attributes=[mid])
        assert AttributeDictUtil.hash(a.to_dict()) == a.hash()

    def test_nested_order_independent(self):
        # Attribute.hash folds sub-attributes into a frozenset, so order shouldn't matter.
        s1 = Attribute(attribute_type_id="biolink:sub", value="x")
        s2 = Attribute(attribute_type_id="biolink:sub", value="y")
        a = Attribute(attribute_type_id="biolink:foo", value=1, attributes=[s1, s2])
        b = Attribute(attribute_type_id="biolink:foo", value=1, attributes=[s2, s1])
        assert AttributeDictUtil.hash(a.to_dict()) == AttributeDictUtil.hash(b.to_dict())


# ============================================================================
# AttributeDictUtil.merge_attribute_lists — parity with Attribute.merge_attribute_lists
# ============================================================================


class TestMergeAttributeLists:
    def _assert_parity(
        self, old: list[Attribute], new: list[Attribute]
    ) -> None:
        old_dicts = [m.to_dict() for m in old]
        new_dicts = [m.to_dict() for m in new]
        Attribute.merge_attribute_lists(old, new)
        AttributeDictUtil.merge_attribute_lists(old_dicts, new_dicts)
        assert old_dicts == [m.to_dict() for m in old]

    def test_union_with_overlap(self):
        self._assert_parity(
            [
                Attribute(attribute_type_id="biolink:a", value=1),
                Attribute(attribute_type_id="biolink:b", value=2),
            ],
            [
                Attribute(attribute_type_id="biolink:b", value=2),
                Attribute(attribute_type_id="biolink:c", value=3),
            ],
        )

    def test_dedupes_within_new(self):
        self._assert_parity(
            [Attribute(attribute_type_id="biolink:a", value=1)],
            [
                Attribute(attribute_type_id="biolink:b", value=2),
                Attribute(attribute_type_id="biolink:b", value=2),
            ],
        )

    def test_empty_new_leaves_old(self):
        self._assert_parity([Attribute(attribute_type_id="biolink:a", value=1)], [])

    def test_empty_old_takes_new(self):
        self._assert_parity([], [Attribute(attribute_type_id="biolink:a", value=1)])


# ============================================================================
# AttributeConstraintDictUtil.hash — parity, incl. the nullable `not` alias
# ============================================================================


class TestAttributeConstraintHashParity:
    @pytest.mark.parametrize("negated", [True, False])
    def test_negated_states(self, negated: bool):
        c = AttributeConstraint(
            id="biolink:foo", name="Foo", operator="==", value=1, negated=negated
        )
        assert AttributeConstraintDictUtil.hash(c.to_dict()) == c.hash()

    def test_default_negated(self):
        c = AttributeConstraint(id="biolink:foo", name="Foo", operator="==", value=1)
        assert AttributeConstraintDictUtil.hash(c.to_dict()) == c.hash()

    def test_with_units(self):
        c = AttributeConstraint(
            id="biolink:foo",
            name="Foo",
            operator=">",
            value=5,
            unit_id="UO:0000221",
            unit_name="gram",
        )
        assert AttributeConstraintDictUtil.hash(c.to_dict()) == c.hash()


# ============================================================================
# AttributeConstraintDictUtil.met_by — parity with AttributeConstraint.met_by
# ============================================================================


def _con(
    operator: str, value: object, *, negated: bool = False
) -> AttributeConstraint:
    return AttributeConstraint(
        id="biolink:foo",
        name="Foo",
        operator=operator,  # type: ignore[arg-type]
        value=value,
        negated=negated,
    )


def _attr(value: object, type_id: str = "biolink:foo") -> Attribute:
    return Attribute(attribute_type_id=type_id, value=value)


def _assert_met_by_parity(
    con: AttributeConstraint, attribute: Attribute | MetaAttribute
) -> None:
    assert AttributeConstraintDictUtil.met_by(
        con.to_dict(), attribute.to_dict()
    ) == con.met_by(attribute)


class TestAttributeConstraintMetByAttribute:
    @pytest.mark.parametrize(
        ("operator", "con_value", "attr_value"),
        [
            ("==", 1, 1),
            ("==", 1, 2),
            ("==", 2, [1, 2, 3]),
            ("==", [2, 3], 2),
            ("==", [4, 5], [1, 2, 3]),
            ("===", [1, 2, 3], [1, 2, 3]),
            ("===", [1, 2, 3], [3, 2, 1]),
            ("===", [1], 1),
            (">", 5, 10),
            (">", 5, 3),
            ("<", 5, 3),
            ("<", 5, 10),
            ("matches", "^bio", "biolink:x"),
            ("matches", "^xyz", "biolink:x"),
        ],
    )
    def test_operators(self, operator: str, con_value: object, attr_value: object):
        _assert_met_by_parity(_con(operator, con_value), _attr(attr_value))

    def test_negated_flips(self):
        _assert_met_by_parity(_con("==", 1, negated=True), _attr(1))
        _assert_met_by_parity(_con("==", 1, negated=True), _attr(2))

    def test_type_id_mismatch(self):
        _assert_met_by_parity(_con("==", 1), _attr(1, type_id="biolink:other"))


class TestAttributeConstraintMetByMetaAttribute:
    @pytest.mark.parametrize("constraint_use", [True, False])
    def test_constraint_use_states(self, constraint_use: bool):
        _assert_met_by_parity(
            _con("==", 1),
            MetaAttribute(
                attribute_type_id="biolink:foo", constraint_use=constraint_use
            ),
        )

    def test_type_id_mismatch(self):
        _assert_met_by_parity(
            _con("==", 1),
            MetaAttribute(attribute_type_id="biolink:other", constraint_use=True),
        )


# ============================================================================
# AttributeConstraintDictUtil.set_met_by — parity with AttributeConstraint.set_met_by
# ============================================================================


class TestAttributeConstraintSetMetBy:
    def _assert_parity(
        self,
        constraints: list[AttributeConstraint],
        attributes: list[Attribute],
    ) -> None:
        result = AttributeConstraintDictUtil.set_met_by(
            [c.to_dict() for c in constraints], [a.to_dict() for a in attributes]
        )
        assert result == AttributeConstraint.set_met_by(constraints, attributes)

    def test_empty_constraints_is_true(self):
        self._assert_parity([], [_attr(1)])

    def test_constraints_but_no_attributes_is_false(self):
        self._assert_parity([_con("==", 1)], [])

    def test_all_constraints_met(self):
        self._assert_parity(
            [_con("==", 1), _con("==", 2, negated=True)],
            [_attr(1)],
        )

    def test_one_constraint_unmet(self):
        self._assert_parity(
            [_con("==", 1), _con("==", 99)],
            [_attr(1)],
        )

    def test_multiple_attributes_grouped_by_type(self):
        self._assert_parity(
            [_con("==", 1)],
            [_attr(0), _attr(1), _attr(2, type_id="biolink:other")],
        )
