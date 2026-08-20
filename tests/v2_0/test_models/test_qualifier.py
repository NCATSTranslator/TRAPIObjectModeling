"""Tests for translator_tom.v2_0.models.qualifier.

In TRAPI 2.0 a qualifier constraint is a plain ``QualifierSetConstraint`` mapping
(``dict[qualifier_type_id, qualifier_value]``); the matching/inversion helpers
live as static methods on ``Qualifier``.
"""

import pytest
from pydantic import ValidationError

from translator_tom import (
    MetaQualifier,
    Qualifier,
)
from translator_tom.v2_0.models.qualifier import QualifierSetConstraint


class TestQualifierBasics:
    def test_required_fields(self):
        q = Qualifier(
            qualifier_type_id="biolink:subject_aspect_qualifier",
            qualifier_value="activity",
        )
        assert q.qualifier_type_id == "biolink:subject_aspect_qualifier"
        assert q.qualifier_value == "activity"

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            Qualifier(
                qualifier_type_id="biolink:subject_aspect_qualifier",
                qualifier_value="activity",
                bogus="x",  # type: ignore[call-arg]
            )


class TestConstraintMetBy:
    def test_empty_constraint_satisfied_trivially(self):
        # No type/value pairs to violate.
        assert Qualifier.constraint_met_by({}, []) is True

    def test_satisfied_by_matching_qualifier(self):
        q = Qualifier(
            qualifier_type_id="biolink:subject_aspect_qualifier",
            qualifier_value="activity",
        )
        constraint: QualifierSetConstraint = {
            "biolink:subject_aspect_qualifier": "activity"
        }
        assert Qualifier.constraint_met_by(constraint, [q]) is True

    def test_unsatisfied_when_no_matching_type(self):
        provided = Qualifier(
            qualifier_type_id="biolink:object_aspect_qualifier",
            qualifier_value="activity",
        )
        constraint: QualifierSetConstraint = {
            "biolink:subject_aspect_qualifier": "activity"
        }
        assert Qualifier.constraint_met_by(constraint, [provided]) is False

    def test_unsatisfied_when_value_disjoint(self):
        provided = Qualifier(
            qualifier_type_id="biolink:subject_aspect_qualifier",
            qualifier_value="abundance",
        )
        constraint: QualifierSetConstraint = {
            "biolink:subject_aspect_qualifier": "activity"
        }
        # `activity` and `abundance` are sibling enum values; neither has the
        # other as a descendant, so the constraint is unmet.
        assert Qualifier.constraint_met_by(constraint, [provided]) is False

    def test_meta_qualifier_applicable_values(self):
        # When fed MetaQualifiers, the constraint checks against
        # applicable_values for value membership.
        meta = MetaQualifier(
            qualifier_type_id="biolink:subject_aspect_qualifier",
            applicable_values=["activity", "abundance"],
        )
        constraint: QualifierSetConstraint = {
            "biolink:subject_aspect_qualifier": "activity"
        }
        assert Qualifier.constraint_met_by(constraint, [meta]) is True

    def test_meta_qualifier_applicable_values_none_is_wildcard(self):
        # MetaQualifier.applicable_values=None means "any value allowed".
        constraint: QualifierSetConstraint = {
            "biolink:object_aspect_qualifier": "secretion",
            "biolink:object_direction_qualifier": "increased",
        }
        op_qualifiers_wildcard = [
            MetaQualifier(
                qualifier_type_id="biolink:object_aspect_qualifier",
                applicable_values=None,
            ),
            MetaQualifier(
                qualifier_type_id="biolink:object_direction_qualifier",
                applicable_values=None,
            ),
        ]
        assert Qualifier.constraint_met_by(constraint, op_qualifiers_wildcard) is True

    # NOTE: the 1.6 "explicit empty applicable_values is not a wildcard" case is
    # gone in 2.0 — the schema now requires `applicable_values` minItems:1, so an
    # empty list is unconstructible. `constraint_met_by` still distinguishes
    # None (wildcard) from a populated list (covered by the two tests above).

    def test_meta_qualifier_missing_type_fails_even_with_wildcard_values(self):
        # Wildcard applicable_values must not bypass the type-id check.
        constraint: QualifierSetConstraint = {
            "biolink:object_aspect_qualifier": "secretion",
        }
        op_qualifiers_wrong_type = [
            MetaQualifier(
                qualifier_type_id="biolink:species_context_qualifier",
                applicable_values=None,
            ),
        ]
        assert (
            Qualifier.constraint_met_by(constraint, op_qualifiers_wrong_type) is False
        )


class TestConstraintSetMetBy:
    def test_empty_constraint_list_satisfied_trivially(self):
        assert Qualifier.constraint_set_met_by([], []) is True

    def test_non_empty_constraints_but_no_qualifiers_fails(self):
        constraint: QualifierSetConstraint = {
            "biolink:subject_aspect_qualifier": "activity"
        }
        assert Qualifier.constraint_set_met_by([constraint], []) is False

    def test_or_relationship_across_constraints(self):
        q = Qualifier(
            qualifier_type_id="biolink:subject_aspect_qualifier",
            qualifier_value="activity",
        )
        # Only the second constraint matches; OR means the set is satisfied.
        unmet: QualifierSetConstraint = {"biolink:object_aspect_qualifier": "activity"}
        met: QualifierSetConstraint = {"biolink:subject_aspect_qualifier": "activity"}
        assert Qualifier.constraint_set_met_by([unmet, met], [q]) is True


class TestGetConstraintInverse:
    def test_subject_to_object(self):
        constraint: QualifierSetConstraint = {
            "biolink:subject_aspect_qualifier": "activity"
        }
        inverse = Qualifier.get_constraint_inverse(constraint)
        assert inverse == {"biolink:object_aspect_qualifier": "activity"}

    def test_object_to_subject(self):
        constraint: QualifierSetConstraint = {
            "biolink:object_aspect_qualifier": "activity"
        }
        inverse = Qualifier.get_constraint_inverse(constraint)
        assert "biolink:subject_aspect_qualifier" in inverse

    def test_qualified_predicate_uses_predicate_inverse(self):
        # `treats` and `treated_by` are inverse predicates in biolink.
        constraint: QualifierSetConstraint = {
            "biolink:qualified_predicate": "biolink:treats"
        }
        inverse = Qualifier.get_constraint_inverse(constraint)
        assert inverse == {"biolink:qualified_predicate": "biolink:treated_by"}

    def test_does_not_mutate_original(self):
        constraint: QualifierSetConstraint = {
            "biolink:subject_aspect_qualifier": "activity"
        }
        Qualifier.get_constraint_inverse(constraint)
        assert constraint == {"biolink:subject_aspect_qualifier": "activity"}

    def test_raises_when_uninvertible(self):
        # Not subject/object/qualified_predicate => no rule for inverse.
        constraint: QualifierSetConstraint = {
            "biolink:anatomical_context_qualifier": "x"
        }
        with pytest.raises(ValueError, match="Cannot invert qualifier of type"):
            Qualifier.get_constraint_inverse(constraint)
