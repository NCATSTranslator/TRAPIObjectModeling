"""Tests for translator_tom.v2_0.models.path_constraint."""

import pytest
from pydantic import ValidationError

from translator_tom import PathConstraint


class TestPathConstraintBasics:
    def test_default_construction(self):
        c = PathConstraint()
        assert c.required_intermediate_categories is None

    def test_with_categories(self):
        c = PathConstraint(required_intermediate_categories=["biolink:Gene"])
        assert c.required_intermediate_categories == ["biolink:Gene"]

    def test_min_length_enforced(self):
        # When provided, the list must have at least one item.
        with pytest.raises(ValidationError):
            PathConstraint(required_intermediate_categories=[])


class TestRequiredIntermediateCategoriesList:
    def test_empty_when_none(self):
        assert PathConstraint().required_intermediate_categories_list == []

    def test_returns_list_when_set(self):
        c = PathConstraint(
            required_intermediate_categories=["biolink:Gene", "biolink:Disease"]
        )
        assert c.required_intermediate_categories_list == [
            "biolink:Gene",
            "biolink:Disease",
        ]
