"""Tests for translator_tom.models.meta_qualifier."""

import pytest
from pydantic import ValidationError

from translator_tom import MetaQualifier


class TestMetaQualifierBasics:
    def test_required_field(self):
        q = MetaQualifier(qualifier_type_id="biolink:subject_aspect_qualifier")
        assert q.qualifier_type_id == "biolink:subject_aspect_qualifier"
        assert q.applicable_values is None

    def test_qualifier_type_id_required(self):
        with pytest.raises(ValidationError):
            MetaQualifier()  # type: ignore[call-arg]


class TestMetaQualifierApplicableValuesList:
    def test_returns_empty_when_none(self):
        q = MetaQualifier(qualifier_type_id="biolink:subject_aspect_qualifier")
        assert q.applicable_values_list == []

    def test_returns_list_when_set(self):
        q = MetaQualifier(
            qualifier_type_id="biolink:subject_aspect_qualifier",
            applicable_values=["activity", "abundance"],
        )
        assert q.applicable_values_list == ["activity", "abundance"]
