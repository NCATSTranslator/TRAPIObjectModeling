"""Tests for the `*DictUtil` sibling classes in `model_dicts/qualifier.py`.

The util classes reimplement the utility methods of the `QualifierConstraint`
Pydantic model for its `TypedDict` equivalent. Tests assert parity by comparing
dict-util results against the model operating on the same data.
"""

from __future__ import annotations

import pytest

from translator_tom.model_dicts.qualifier import QualifierConstraintDictUtil
from translator_tom.models.meta_qualifier import MetaQualifier
from translator_tom.models.qualifier import Qualifier, QualifierConstraint


def _q(type_id: str, value: str) -> Qualifier:
    return Qualifier(qualifier_type_id=type_id, qualifier_value=value)


def _qc(*pairs: tuple[str, str]) -> QualifierConstraint:
    return QualifierConstraint(qualifier_set=[_q(t, v) for t, v in pairs])


# ============================================================================
# QualifierConstraintDictUtil.new
# ============================================================================


class TestNew:
    def test_matches_model(self):
        assert QualifierConstraintDictUtil.new() == QualifierConstraint.new().to_dict()
        assert QualifierConstraintDictUtil.new() == {"qualifier_set": []}


# ============================================================================
# QualifierConstraintDictUtil.hash — parity (base hash, recurses into Qualifier)
# ============================================================================


class TestHashParity:
    def test_empty_set(self):
        qc = QualifierConstraint(qualifier_set=[])
        assert QualifierConstraintDictUtil.hash(qc.to_dict()) == qc.hash()

    def test_populated_set(self):
        qc = _qc(
            ("biolink:subject_aspect_qualifier", "activity"),
            ("biolink:object_direction_qualifier", "increased"),
        )
        assert QualifierConstraintDictUtil.hash(qc.to_dict()) == qc.hash()


# ============================================================================
# QualifierConstraintDictUtil.met_by — parity with QualifierConstraint.met_by
# ============================================================================


def _assert_met_by_parity(
    qc: QualifierConstraint,
    qualifiers: list[Qualifier] | list[MetaQualifier],
) -> None:
    dicts = [q.to_dict() for q in qualifiers]
    assert QualifierConstraintDictUtil.met_by(qc.to_dict(), dicts) == qc.met_by(
        qualifiers
    )


class TestMetByQualifiers:
    def test_empty_constraint_is_met(self):
        _assert_met_by_parity(QualifierConstraint(qualifier_set=[]), [])

    def test_no_qualifiers_fails_nonempty_constraint(self):
        _assert_met_by_parity(_qc(("biolink:subject_aspect_qualifier", "activity")), [])

    def test_matching_qualifier(self):
        _assert_met_by_parity(
            _qc(("biolink:subject_aspect_qualifier", "activity")),
            [_q("biolink:subject_aspect_qualifier", "activity")],
        )

    def test_type_mismatch(self):
        _assert_met_by_parity(
            _qc(("biolink:subject_aspect_qualifier", "activity")),
            [_q("biolink:object_aspect_qualifier", "activity")],
        )

    def test_value_mismatch(self):
        _assert_met_by_parity(
            _qc(("biolink:subject_aspect_qualifier", "activity")),
            [_q("biolink:subject_aspect_qualifier", "abundance")],
        )


class TestMetByMetaQualifiers:
    def test_applicable_values_match(self):
        _assert_met_by_parity(
            _qc(("biolink:subject_aspect_qualifier", "activity")),
            [
                MetaQualifier(
                    qualifier_type_id="biolink:subject_aspect_qualifier",
                    applicable_values=["activity", "abundance"],
                )
            ],
        )

    def test_applicable_values_none_is_wildcard(self):
        _assert_met_by_parity(
            _qc(("biolink:object_aspect_qualifier", "secretion")),
            [
                MetaQualifier(
                    qualifier_type_id="biolink:object_aspect_qualifier",
                    applicable_values=None,
                )
            ],
        )

    def test_applicable_values_empty_is_not_wildcard(self):
        _assert_met_by_parity(
            _qc(("biolink:object_aspect_qualifier", "secretion")),
            [
                MetaQualifier(
                    qualifier_type_id="biolink:object_aspect_qualifier",
                    applicable_values=[],
                )
            ],
        )


# ============================================================================
# QualifierConstraintDictUtil.set_met_by — parity with the model
# ============================================================================


class TestSetMetBy:
    def _assert_parity(
        self,
        constraints: list[QualifierConstraint],
        qualifiers: list[Qualifier],
    ) -> None:
        result = QualifierConstraintDictUtil.set_met_by(
            [c.to_dict() for c in constraints], [q.to_dict() for q in qualifiers]
        )
        assert result == QualifierConstraint.set_met_by(constraints, qualifiers)

    def test_empty_constraints_is_true(self):
        self._assert_parity([], [_q("biolink:subject_aspect_qualifier", "activity")])

    def test_constraints_but_no_qualifiers_is_false(self):
        self._assert_parity(
            [_qc(("biolink:subject_aspect_qualifier", "activity"))], []
        )

    def test_any_constraint_met(self):
        self._assert_parity(
            [
                _qc(("biolink:subject_aspect_qualifier", "abundance")),
                _qc(("biolink:subject_aspect_qualifier", "activity")),
            ],
            [_q("biolink:subject_aspect_qualifier", "activity")],
        )


# ============================================================================
# QualifierConstraintDictUtil.get_inverse — parity with QualifierConstraint.get_inverse
# ============================================================================


class TestGetInverse:
    def _assert_parity(self, qc: QualifierConstraint) -> None:
        assert (
            QualifierConstraintDictUtil.get_inverse(qc.to_dict())
            == qc.get_inverse().to_dict()
        )

    def test_subject_to_object(self):
        self._assert_parity(_qc(("biolink:subject_aspect_qualifier", "activity")))

    def test_object_to_subject(self):
        self._assert_parity(_qc(("biolink:object_direction_qualifier", "increased")))

    def test_qualified_predicate_value_inverted(self):
        self._assert_parity(_qc(("biolink:qualified_predicate", "biolink:causes")))

    def test_uninvertible_raises(self):
        qc = _qc(("biolink:qualified_predicate", "biolink:has_count"))
        with pytest.raises(ValueError, match="non-inversible predicate"):
            QualifierConstraintDictUtil.get_inverse(qc.to_dict())
