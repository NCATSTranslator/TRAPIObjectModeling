"""Tests for translator_tom.v2_0.validation._util."""

import pytest

from translator_tom.v2_0.validation._util import (
    _biolink_element_verdict,
    validate_biolink_element,
    validate_predicate,
)


@pytest.fixture(autouse=True)
def _clear_verdict_cache():
    """Reset the verdict cache so per-test cache_info counts are deterministic."""
    _biolink_element_verdict.cache_clear()
    yield
    _biolink_element_verdict.cache_clear()


class TestValidateBiolinkElement:
    def test_valid_predicate_passes(self):
        assert validate_predicate("biolink:related_to") == ([], [])

    def test_invalid_element_errors_at_location(self):
        location = ("edges", "e1", "predicate")
        warnings, errors = validate_biolink_element(
            "biolink:not_a_real_predicate", "predicate", location
        )
        assert warnings == []
        assert len(errors) == 1
        assert errors[0].location == location
        assert "not a valid BioLink predicate" in errors[0].message

    def test_same_element_two_locations_two_located_errors(self):
        # One cached verdict must still surface at each caller's own location.
        loc_a = ("edges", "eA", "predicate")
        loc_b = ("edges", "eB", "predicate")
        _, errors_a = validate_biolink_element(
            "biolink:not_a_real_predicate", "predicate", loc_a
        )
        _, errors_b = validate_biolink_element(
            "biolink:not_a_real_predicate", "predicate", loc_b
        )
        assert errors_a[0].location == loc_a
        assert errors_b[0].location == loc_b
        assert errors_a[0].message == errors_b[0].message

    def test_deprecated_element_warns(self):
        warnings, errors = validate_biolink_element(
            "biolink:increases_amount_or_activity_of", "predicate", ("edges", "e2")
        )
        assert errors == []
        assert len(warnings) == 1
        assert warnings[0].location == ("edges", "e2")
        assert "is deprecated" in warnings[0].message


class TestVerdictCaching:
    def test_repeated_calls_hit_the_cache(self):
        # First call misses, subsequent calls with the same element+type hit.
        validate_biolink_element(
            "biolink:not_a_real_predicate", "predicate", ("loc", "1")
        )
        first = _biolink_element_verdict.cache_info()
        assert first.misses == 1
        assert first.hits == 0

        validate_biolink_element(
            "biolink:not_a_real_predicate", "predicate", ("loc", "2")
        )
        second = _biolink_element_verdict.cache_info()
        assert second.misses == 1  # no new computation
        assert second.hits == 1  # served from cache
