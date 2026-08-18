"""Tests for the `*DictUtil` sibling class in `model_dicts/path_constraint.py`.

`PathConstraintDictUtil` reimplements `PathConstraint`'s utility methods for its
`TypedDict` equivalent; tests assert parity with the Pydantic behaviour.

In TRAPI 2.0 the field is `required_intermediate_categories` (accessor
`required_intermediate_categories_list`) and, when present, must be non-empty.
"""

from __future__ import annotations

from translator_tom.model_dicts.path_constraint import (
    PathConstraintDict,
    PathConstraintDictUtil,
)
from translator_tom.models.path_constraint import PathConstraint

# ============================================================================
# PathConstraintDictUtil.required_intermediate_categories_list
# ============================================================================


class TestRequiredIntermediateCategoriesList:
    def test_missing_key_returns_empty(self):
        assert PathConstraintDictUtil.required_intermediate_categories_list({}) == []

    def test_explicit_none_returns_empty(self):
        constraint: PathConstraintDict = {"required_intermediate_categories": None}
        assert (
            PathConstraintDictUtil.required_intermediate_categories_list(constraint)
            == []
        )

    def test_populated_returns_value(self):
        constraint: PathConstraintDict = {
            "required_intermediate_categories": ["biolink:Gene"]
        }
        assert PathConstraintDictUtil.required_intermediate_categories_list(
            constraint
        ) == ["biolink:Gene"]

    def test_parity_with_model(self):
        model = PathConstraint(required_intermediate_categories=["biolink:Gene"])
        assert (
            PathConstraintDictUtil.required_intermediate_categories_list(
                model.to_dict()
            )
            == model.required_intermediate_categories_list
        )


# ============================================================================
# PathConstraintDictUtil.hash — parity with PathConstraint.hash
# ============================================================================


class TestHashParity:
    def test_empty(self):
        model = PathConstraint()
        assert PathConstraintDictUtil.hash(model.to_dict()) == model.hash()

    def test_populated(self):
        model = PathConstraint(
            required_intermediate_categories=["biolink:Gene", "biolink:Drug"]
        )
        assert PathConstraintDictUtil.hash(model.to_dict()) == model.hash()
