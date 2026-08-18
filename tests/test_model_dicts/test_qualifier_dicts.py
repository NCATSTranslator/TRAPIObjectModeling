"""Tests for the `*DictUtil` sibling class in `model_dicts/qualifier.py`.

In TRAPI 2.0 the `QualifierConstraint` model/dict is gone: a
`QualifierSetConstraint` is a plain `dict[qualifier_type_id, qualifier_value]`
and the matching/inversion helpers are static methods on `QualifierDictUtil`
(mirroring `Qualifier`). Tests assert parity by comparing dict-util results
against the model operating on the same data.
"""

from __future__ import annotations

import pytest

from translator_tom import MetaQualifier, Qualifier
from translator_tom.model_dicts.qualifier import QualifierDictUtil
from translator_tom.models.qualifier import QualifierSetConstraint


def _q(type_id: str, value: str) -> Qualifier:
    return Qualifier(qualifier_type_id=type_id, qualifier_value=value)


# ============================================================================
# QualifierDictUtil.hash — parity with Qualifier.hash
# ============================================================================


class TestHashParity:
    def test_parity(self):
        q = _q("biolink:subject_aspect_qualifier", "activity")
        assert QualifierDictUtil.hash(q.to_dict()) == q.hash()


# ============================================================================
# QualifierDictUtil.constraint_met_by — parity with Qualifier.constraint_met_by
# ============================================================================


def _assert_met_by_parity(
    constraint: QualifierSetConstraint,
    qualifiers: list[Qualifier] | list[MetaQualifier],
) -> None:
    dicts = [q.to_dict() for q in qualifiers]
    assert QualifierDictUtil.constraint_met_by(
        constraint, dicts
    ) == Qualifier.constraint_met_by(constraint, qualifiers)


class TestConstraintMetByQualifiers:
    def test_empty_constraint_is_met(self):
        _assert_met_by_parity({}, [])

    def test_no_qualifiers_fails_nonempty_constraint(self):
        _assert_met_by_parity({"biolink:subject_aspect_qualifier": "activity"}, [])

    def test_matching_qualifier(self):
        _assert_met_by_parity(
            {"biolink:subject_aspect_qualifier": "activity"},
            [_q("biolink:subject_aspect_qualifier", "activity")],
        )

    def test_type_mismatch(self):
        _assert_met_by_parity(
            {"biolink:subject_aspect_qualifier": "activity"},
            [_q("biolink:object_aspect_qualifier", "activity")],
        )

    def test_value_mismatch(self):
        _assert_met_by_parity(
            {"biolink:subject_aspect_qualifier": "activity"},
            [_q("biolink:subject_aspect_qualifier", "abundance")],
        )


class TestConstraintMetByMetaQualifiers:
    def test_applicable_values_match(self):
        _assert_met_by_parity(
            {"biolink:subject_aspect_qualifier": "activity"},
            [
                MetaQualifier(
                    qualifier_type_id="biolink:subject_aspect_qualifier",
                    applicable_values=["activity", "abundance"],
                )
            ],
        )

    def test_applicable_values_none_is_wildcard(self):
        _assert_met_by_parity(
            {"biolink:object_aspect_qualifier": "secretion"},
            [
                MetaQualifier(
                    qualifier_type_id="biolink:object_aspect_qualifier",
                    applicable_values=None,
                )
            ],
        )

    # NOTE: the 1.6 "explicit empty applicable_values is not a wildcard" case is gone
    # in 2.0 — the schema now requires `applicable_values` minItems:1, so an empty list
    # is unconstructible. None (wildcard) vs a populated list is covered above.


# ============================================================================
# QualifierDictUtil.constraint_set_met_by — parity with the model
# ============================================================================


class TestConstraintSetMetBy:
    def _assert_parity(
        self,
        constraints: list[QualifierSetConstraint],
        qualifiers: list[Qualifier],
    ) -> None:
        dicts = [q.to_dict() for q in qualifiers]
        assert QualifierDictUtil.constraint_set_met_by(
            constraints, dicts
        ) == Qualifier.constraint_set_met_by(constraints, qualifiers)

    def test_empty_constraints_is_true(self):
        self._assert_parity([], [_q("biolink:subject_aspect_qualifier", "activity")])

    def test_constraints_but_no_qualifiers_is_false(self):
        self._assert_parity([{"biolink:subject_aspect_qualifier": "activity"}], [])

    def test_any_constraint_met(self):
        self._assert_parity(
            [
                {"biolink:subject_aspect_qualifier": "abundance"},
                {"biolink:subject_aspect_qualifier": "activity"},
            ],
            [_q("biolink:subject_aspect_qualifier", "activity")],
        )


# ============================================================================
# QualifierDictUtil.get_constraint_inverse — parity with the model
# ============================================================================


class TestGetConstraintInverse:
    def _assert_parity(self, constraint: QualifierSetConstraint) -> None:
        assert QualifierDictUtil.get_constraint_inverse(
            constraint
        ) == Qualifier.get_constraint_inverse(constraint)

    def test_subject_to_object(self):
        self._assert_parity({"biolink:subject_aspect_qualifier": "activity"})

    def test_object_to_subject(self):
        self._assert_parity({"biolink:object_direction_qualifier": "increased"})

    def test_qualified_predicate_value_inverted(self):
        self._assert_parity({"biolink:qualified_predicate": "biolink:treats"})

    def test_does_not_mutate_original(self):
        constraint: QualifierSetConstraint = {
            "biolink:subject_aspect_qualifier": "activity"
        }
        QualifierDictUtil.get_constraint_inverse(constraint)
        assert constraint == {"biolink:subject_aspect_qualifier": "activity"}

    def test_uninvertible_raises(self):
        constraint: QualifierSetConstraint = {
            "biolink:qualified_predicate": "biolink:has_count"
        }
        with pytest.raises(ValueError, match="Cannot invert qualified_predicate"):
            QualifierDictUtil.get_constraint_inverse(constraint)
