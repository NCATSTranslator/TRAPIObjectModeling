"""Tests for translator_tom.models.qualifier."""

import pytest
from pydantic import ValidationError

from translator_tom import (
    MetaQualifier,
    Qualifier,
    QualifierConstraint,
)


class TestQualifierBasics:
    def test_required_fields(self):
        q = Qualifier(
            qualifier_type_id="biolink:subject_aspect_qualifier",
            qualifier_value="activity",
        )
        assert q.qualifier_type_id == "biolink:subject_aspect_qualifier"
        assert q.qualifier_value == "activity"

    def test_pattern_enforced(self):
        # Pattern requires snake_case after biolink:
        with pytest.raises(ValidationError):
            Qualifier(
                qualifier_type_id="biolink:NotSnakeCase",
                qualifier_value="x",
            )

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            Qualifier(
                qualifier_type_id="biolink:subject_aspect_qualifier",
                qualifier_value="activity",
                bogus="x",  # type: ignore[call-arg]
            )


class TestQualifierConstraintBasics:
    def test_required_field(self):
        c = QualifierConstraint(qualifier_set=[])
        assert c.qualifier_set == []

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            QualifierConstraint(qualifier_set=[], bogus="x")  # type: ignore[call-arg]

    def test_new_returns_empty(self):
        c = QualifierConstraint.new()
        assert c.qualifier_set == []


class TestQualifierConstraintMetBy:
    def test_empty_constraint_set_satisfied_trivially(self):
        # No constraints to violate.
        c = QualifierConstraint(qualifier_set=[])
        assert c.met_by([]) is True

    def test_satisfied_by_matching_qualifier(self):
        q = Qualifier(
            qualifier_type_id="biolink:subject_aspect_qualifier",
            qualifier_value="activity",
        )
        c = QualifierConstraint(qualifier_set=[q])
        assert c.met_by([q]) is True

    def test_unsatisfied_when_no_matching_type(self):
        constraint = Qualifier(
            qualifier_type_id="biolink:subject_aspect_qualifier",
            qualifier_value="activity",
        )
        # Different type id => never matches.
        provided = Qualifier(
            qualifier_type_id="biolink:object_aspect_qualifier",
            qualifier_value="activity",
        )
        c = QualifierConstraint(qualifier_set=[constraint])
        assert c.met_by([provided]) is False

    def test_unsatisfied_when_value_disjoint(self):
        constraint = Qualifier(
            qualifier_type_id="biolink:subject_aspect_qualifier",
            qualifier_value="activity",
        )
        provided = Qualifier(
            qualifier_type_id="biolink:subject_aspect_qualifier",
            qualifier_value="abundance",
        )
        c = QualifierConstraint(qualifier_set=[constraint])
        # `activity` and `abundance` are sibling enum values; neither has the
        # other as a descendant, so the constraint is unmet.
        assert c.met_by([provided]) is False

    def test_meta_qualifier_applicable_values(self):
        # When fed MetaQualifiers, the constraint checks against
        # applicable_values_list for value membership.
        constraint = Qualifier(
            qualifier_type_id="biolink:subject_aspect_qualifier",
            qualifier_value="activity",
        )
        meta = MetaQualifier(
            qualifier_type_id="biolink:subject_aspect_qualifier",
            applicable_values=["activity", "abundance"],
        )
        c = QualifierConstraint(qualifier_set=[constraint])
        assert c.met_by([meta]) is True


class TestQualifierConstraintGetInverse:
    def test_subject_to_object(self):
        q = Qualifier(
            qualifier_type_id="biolink:subject_aspect_qualifier",
            qualifier_value="activity",
        )
        c = QualifierConstraint(qualifier_set=[q])
        inverse = c.get_inverse()
        assert (
            inverse.qualifier_set[0].qualifier_type_id
            == "biolink:object_aspect_qualifier"
        )
        assert inverse.qualifier_set[0].qualifier_value == "activity"

    def test_object_to_subject(self):
        q = Qualifier(
            qualifier_type_id="biolink:object_aspect_qualifier",
            qualifier_value="activity",
        )
        c = QualifierConstraint(qualifier_set=[q])
        inverse = c.get_inverse()
        assert (
            inverse.qualifier_set[0].qualifier_type_id
            == "biolink:subject_aspect_qualifier"
        )

    def test_qualified_predicate_uses_predicate_inverse(self):
        # `treats` and `treated_by` are inverse predicates in biolink.
        q = Qualifier(
            qualifier_type_id="biolink:qualified_predicate",
            qualifier_value="biolink:treats",
        )
        c = QualifierConstraint(qualifier_set=[q])
        inverse = c.get_inverse()
        assert (
            inverse.qualifier_set[0].qualifier_type_id
            == "biolink:qualified_predicate"
        )
        assert inverse.qualifier_set[0].qualifier_value == "biolink:treated_by"

    def test_does_not_mutate_original(self):
        q = Qualifier(
            qualifier_type_id="biolink:subject_aspect_qualifier",
            qualifier_value="activity",
        )
        c = QualifierConstraint(qualifier_set=[q])
        c.get_inverse()
        assert (
            c.qualifier_set[0].qualifier_type_id
            == "biolink:subject_aspect_qualifier"
        )

    def test_raises_when_uninvertible(self):
        # Not subject/object/qualified_predicate => no rule for inverse.
        q = Qualifier(
            qualifier_type_id="biolink:anatomical_context_qualifier",
            qualifier_value="x",
        )
        c = QualifierConstraint(qualifier_set=[q])
        with pytest.raises(ValueError, match="Cannot inverse qualifier"):
            c.get_inverse()
