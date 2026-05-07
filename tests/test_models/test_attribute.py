"""Tests for translator_tom.models.attribute."""

import pytest
from pydantic import ValidationError

from translator_tom import Attribute, AttributeConstraint
from translator_tom.models.attribute import OperatorEnum
from translator_tom.models.meta_attribute import MetaAttribute


class TestOperatorEnum:
    @pytest.mark.parametrize(
        ("member", "value"),
        [
            (OperatorEnum.EQ, "=="),
            (OperatorEnum.EQ_STRICT, "==="),
            (OperatorEnum.GT, ">"),
            (OperatorEnum.LT, "<"),
            (OperatorEnum.MATCHES, "matches"),
        ],
    )
    def test_values(self, member: OperatorEnum, value: str):
        assert member.value == value
        assert member == value


class TestAttributeBasics:
    def test_required_fields_only(self):
        attr = Attribute(attribute_type_id="biolink:foo", value=1)
        assert attr.attribute_type_id == "biolink:foo"
        assert attr.value == 1
        assert attr.attributes is None

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            Attribute(attribute_type_id="biolink:foo", value=1, bogus="x")  # type: ignore[call-arg]

    def test_round_trip_dict(self):
        original = Attribute(
            attribute_type_id="biolink:foo",
            value=1,
            description="desc",
            attribute_source="source",
        )
        assert Attribute.from_dict(original.to_dict()) == original


class TestValueJsonSchemaNonNull:
    """`value` is non-nullable per spec.

    Runtime validation is intentionally skipped (perf), but the generated JSON
    schema marks the field as non-null via `WithJsonSchema`.
    """

    @staticmethod
    def _value_schema(model_cls: type) -> dict[str, object]:
        """Return the `value` property schema regardless of $defs wrapping."""
        schema = model_cls.model_json_schema()
        if "properties" in schema:
            return schema["properties"]["value"]
        return schema["$defs"][model_cls.__name__]["properties"]["value"]

    def test_attribute_value_json_schema_excludes_null(self):
        assert self._value_schema(Attribute).get("not") == {"type": "null"}

    def test_constraint_value_json_schema_excludes_null(self):
        assert self._value_schema(AttributeConstraint).get("not") == {
            "type": "null"
        }


class TestAttributesListProperty:
    def test_returns_empty_when_none(self):
        attr = Attribute(attribute_type_id="biolink:foo", value=1)
        assert attr.attributes_list == []

    def test_returns_actual_list(self):
        sub = Attribute(attribute_type_id="biolink:bar", value=2)
        attr = Attribute(attribute_type_id="biolink:foo", value=1, attributes=[sub])
        assert attr.attributes_list == [sub]


class TestAttributeHash:
    def test_deterministic(self):
        a = Attribute(attribute_type_id="biolink:foo", value=1)
        b = Attribute(attribute_type_id="biolink:foo", value=1)
        assert a.hash() == b.hash()

    def test_changes_with_value(self):
        a = Attribute(attribute_type_id="biolink:foo", value=1)
        b = Attribute(attribute_type_id="biolink:foo", value=2)
        assert a.hash() != b.hash()

    def test_includes_sub_attributes(self):
        sub_a = Attribute(attribute_type_id="biolink:sub", value="x")
        sub_b = Attribute(attribute_type_id="biolink:sub", value="y")
        a = Attribute(attribute_type_id="biolink:foo", value=1, attributes=[sub_a])
        b = Attribute(attribute_type_id="biolink:foo", value=1, attributes=[sub_b])
        assert a.hash() != b.hash()

    def test_sub_attribute_order_does_not_matter(self):
        # Sub-attributes are hashed via frozenset, so ordering is irrelevant.
        sub1 = Attribute(attribute_type_id="biolink:sub", value="x")
        sub2 = Attribute(attribute_type_id="biolink:sub", value="y")
        a = Attribute(attribute_type_id="biolink:foo", value=1, attributes=[sub1, sub2])
        b = Attribute(attribute_type_id="biolink:foo", value=1, attributes=[sub2, sub1])
        assert a.hash() == b.hash()


class TestMergeAttributeLists:
    def test_appends_new_attribute(self):
        a = Attribute(attribute_type_id="biolink:foo", value=1)
        b = Attribute(attribute_type_id="biolink:bar", value=2)
        old = [a]
        Attribute.merge_attribute_lists(old, [b])
        assert old == [a, b]

    def test_deduplicates_by_hash(self):
        a = Attribute(attribute_type_id="biolink:foo", value=1)
        a_dup = Attribute(attribute_type_id="biolink:foo", value=1)
        old = [a]
        Attribute.merge_attribute_lists(old, [a_dup])
        assert len(old) == 1

    def test_new_replaces_existing_with_same_hash(self):
        # Same hash => new instance overwrites in dict, last one wins.
        a = Attribute(attribute_type_id="biolink:foo", value=1)
        a_dup = Attribute(attribute_type_id="biolink:foo", value=1)
        old = [a]
        Attribute.merge_attribute_lists(old, [a_dup])
        assert old[0] is a_dup

    def test_clears_and_extends_in_place(self):
        a = Attribute(attribute_type_id="biolink:foo", value=1)
        b = Attribute(attribute_type_id="biolink:bar", value=2)
        old = [a]
        original_id = id(old)
        Attribute.merge_attribute_lists(old, [b])
        assert id(old) == original_id


class TestAttributeConstraintBasics:
    def test_required_fields(self):
        c = AttributeConstraint(
            id="biolink:foo", name="Foo", operator="==", value=1
        )
        assert c.id == "biolink:foo"
        assert c.operator == "=="
        assert c.negated is False

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            AttributeConstraint(
                id="biolink:foo",
                name="Foo",
                operator="==",
                value=1,
                bogus="x",  # type: ignore[call-arg]
            )

    def test_invalid_operator_rejected(self):
        with pytest.raises(ValidationError):
            AttributeConstraint(
                id="biolink:foo",
                name="Foo",
                operator="!=",  # type: ignore[arg-type]
                value=1,
            )


class TestAttributeConstraintUnitFields:
    def test_unit_fields_round_trip(self):
        original = AttributeConstraint(
            id="biolink:molecular_mass",
            name="molecular mass",
            operator="==",
            value=57.0,
            unit_id="UO:0000222",
            unit_name="kilodalton",
        )
        restored = AttributeConstraint.from_dict(original.to_dict())
        assert restored.unit_id == "UO:0000222"
        assert restored.unit_name == "kilodalton"


class TestAttributeConstraintHash:
    def test_deterministic(self):
        a = AttributeConstraint(
            id="biolink:foo", name="Foo", operator="==", value=1
        )
        b = AttributeConstraint(
            id="biolink:foo", name="Foo", operator="==", value=1
        )
        assert a.hash() == b.hash()

    def test_differs_when_negated(self):
        a = AttributeConstraint(
            id="biolink:foo", name="Foo", operator="==", value=1
        )
        b = AttributeConstraint(
            id="biolink:foo", name="Foo", operator="==", value=1, negated=True
        )
        assert a.hash() != b.hash()


class TestAttributeConstraintAlias:
    def test_serializes_as_not(self):
        c = AttributeConstraint(
            id="biolink:foo", name="Foo", operator="==", value=1, negated=True
        )
        out = c.to_dict()
        assert out["not"] is True
        assert "negated" not in out

    def test_populate_from_alias(self):
        c = AttributeConstraint.from_dict(
            {"id": "biolink:foo", "name": "Foo", "operator": "==", "value": 1, "not": True}
        )
        assert c.negated is True

    def test_populate_from_python_name(self):
        c = AttributeConstraint.from_dict(
            {
                "id": "biolink:foo",
                "name": "Foo",
                "operator": "==",
                "value": 1,
                "negated": True,
            }
        )
        assert c.negated is True

    def test_round_trip_through_alias(self):
        original = AttributeConstraint(
            id="biolink:foo", name="Foo", operator="==", value=1, negated=True
        )
        restored = AttributeConstraint.from_dict(original.to_dict())
        assert restored.negated is True


# ---- AttributeConstraint.met_by ----------------------------------------------


def _attr(value: object, type_id: str = "biolink:foo") -> Attribute:
    return Attribute(attribute_type_id=type_id, value=value)


def _con(
    operator: str,
    value: object,
    *,
    negated: bool = False,
    type_id: str = "biolink:foo",
) -> AttributeConstraint:
    return AttributeConstraint(
        id=type_id,
        name="Foo",
        operator=operator,  # type: ignore[arg-type]
        value=value,
        negated=negated,
    )


class TestMetByIdMismatch:
    def test_returns_false_when_id_mismatch(self):
        c = _con("==", 1, type_id="biolink:foo")
        a = _attr(1, type_id="biolink:bar")
        assert c.met_by(a) is False


class TestMetByEq:
    def test_scalar_match(self):
        assert _con("==", 1).met_by(_attr(1)) is True

    def test_scalar_mismatch(self):
        assert _con("==", 1).met_by(_attr(2)) is False

    def test_list_attribute_acts_like_in(self):
        # attribute.value is a list; constraint.value scalar; one match suffices.
        assert _con("==", 2).met_by(_attr([1, 2, 3])) is True

    def test_list_constraint_acts_like_in(self):
        # constraint.value is a list; any matching attribute value succeeds.
        assert _con("==", [2, 3]).met_by(_attr(2)) is True

    def test_list_x_list_disjoint_is_false(self):
        assert _con("==", [4, 5]).met_by(_attr([1, 2, 3])) is False

    def test_negated_inverts_result(self):
        assert _con("==", 1, negated=True).met_by(_attr(1)) is False
        assert _con("==", 1, negated=True).met_by(_attr(2)) is True


class TestMetByEqStrict:
    def test_exact_list_match(self):
        assert _con("===", [1, 2, 3]).met_by(_attr([1, 2, 3])) is True

    def test_list_order_matters(self):
        assert _con("===", [1, 2, 3]).met_by(_attr([3, 2, 1])) is False

    def test_does_not_broadcast_lists(self):
        # === requires exact equality; scalar 1 != [1].
        assert _con("===", [1]).met_by(_attr(1)) is False

    def test_negated(self):
        assert (
            _con("===", [1, 2, 3], negated=True).met_by(_attr([1, 2, 3])) is False
        )


class TestMetByGtLt:
    def test_gt_true(self):
        assert _con(">", 5).met_by(_attr(10)) is True

    def test_gt_false(self):
        assert _con(">", 5).met_by(_attr(3)) is False

    def test_lt_true(self):
        assert _con("<", 5).met_by(_attr(3)) is True

    def test_lt_false(self):
        assert _con("<", 5).met_by(_attr(10)) is False

    def test_non_numeric_values_skipped(self):
        # Non-numeric values are filtered out of the comparison.
        assert _con(">", 5).met_by(_attr("not a number")) is False

    def test_list_attribute_any_match(self):
        assert _con(">", 5).met_by(_attr([1, 2, 10])) is True


class TestMetByMatches:
    def test_basic_match(self):
        assert _con("matches", r"hel+o").met_by(_attr("hello world")) is True

    def test_no_match(self):
        assert _con("matches", r"^xyz$").met_by(_attr("hello")) is False

    def test_non_string_attr_skipped(self):
        assert _con("matches", r"\d+").met_by(_attr(123)) is False

    def test_list_attribute_any_match(self):
        assert _con("matches", r"^foo$").met_by(_attr(["bar", "foo", "baz"])) is True

    def test_negated(self):
        assert (
            _con("matches", r"hello", negated=True).met_by(_attr("hello world"))
            is False
        )


class TestMetByMetaAttribute:
    def test_id_match_with_constraint_use_true(self):
        c = _con("==", 1)
        m = MetaAttribute(attribute_type_id="biolink:foo", constraint_use=True)
        assert c.met_by(m) is True

    def test_id_match_with_constraint_use_none(self):
        # `None is not False` -> True.
        c = _con("==", 1)
        m = MetaAttribute(attribute_type_id="biolink:foo", constraint_use=None)
        assert c.met_by(m) is True

    def test_id_match_with_constraint_use_false(self):
        c = _con("==", 1)
        m = MetaAttribute(attribute_type_id="biolink:foo", constraint_use=False)
        assert c.met_by(m) is False

    def test_id_mismatch(self):
        c = _con("==", 1, type_id="biolink:foo")
        m = MetaAttribute(attribute_type_id="biolink:bar", constraint_use=True)
        assert c.met_by(m) is False


class TestSetMetBy:
    def test_empty_constraints_returns_true(self):
        assert AttributeConstraint.set_met_by([], []) is True

    def test_constraints_but_no_attributes_returns_false(self):
        assert AttributeConstraint.set_met_by([_con("==", 1)], []) is False

    def test_all_constraints_satisfied(self):
        c1 = _con("==", 1, type_id="biolink:a")
        c2 = _con("==", 2, type_id="biolink:b")
        attrs = [_attr(1, type_id="biolink:a"), _attr(2, type_id="biolink:b")]
        assert AttributeConstraint.set_met_by([c1, c2], attrs) is True

    def test_one_constraint_unsatisfied(self):
        c1 = _con("==", 1, type_id="biolink:a")
        c2 = _con("==", 99, type_id="biolink:b")
        attrs = [_attr(1, type_id="biolink:a"), _attr(2, type_id="biolink:b")]
        assert AttributeConstraint.set_met_by([c1, c2], attrs) is False

    def test_multiple_attrs_same_id_or_satisfies(self):
        # set_met_by groups attrs by id; only one attr per id needs to match.
        c = _con("==", 2, type_id="biolink:a")
        attrs = [_attr(1, type_id="biolink:a"), _attr(2, type_id="biolink:a")]
        assert AttributeConstraint.set_met_by([c], attrs) is True

    def test_constraint_with_no_matching_id_is_unsatisfied(self):
        c = _con("==", 1, type_id="biolink:nonexistent")
        attrs = [_attr(1, type_id="biolink:a")]
        assert AttributeConstraint.set_met_by([c], attrs) is False
