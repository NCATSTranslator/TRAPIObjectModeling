"""Tests for translator_tom.models.path_constraint."""

import pytest
from pydantic import ValidationError

from translator_tom import PathConstraint


class TestPathConstraintBasics:
    def test_default_construction(self):
        c = PathConstraint()
        assert c.intermediate_categories is None

    def test_with_categories(self):
        c = PathConstraint(intermediate_categories=["biolink:Gene"])
        assert c.intermediate_categories == ["biolink:Gene"]

    def test_min_length_enforced(self):
        # When provided, the list must have at least one item.
        with pytest.raises(ValidationError):
            PathConstraint(intermediate_categories=[])


class TestIntermediateCategoriesList:
    def test_empty_when_none(self):
        assert PathConstraint().intermediate_categories_list == []

    def test_returns_list_when_set(self):
        c = PathConstraint(
            intermediate_categories=["biolink:Gene", "biolink:Disease"]
        )
        assert c.intermediate_categories_list == ["biolink:Gene", "biolink:Disease"]
