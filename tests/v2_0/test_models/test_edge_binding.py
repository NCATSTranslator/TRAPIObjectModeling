"""Tests for translator_tom.v2_0.models.edge_binding."""

import pytest
from pydantic import ValidationError

from translator_tom import EdgeBinding


class TestEdgeBindingConstruction:
    def test_required_fields(self):
        eb = EdgeBinding(ids=["e1"])
        assert eb.ids == ["e1"]

    def test_ids_required(self):
        with pytest.raises(ValidationError):
            EdgeBinding()  # type: ignore[call-arg]

    def test_ids_min_length(self):
        with pytest.raises(ValidationError):
            EdgeBinding(ids=[])


class TestEdgeBindingHash:
    def test_deterministic(self):
        a = EdgeBinding(ids=["e1"])
        b = EdgeBinding(ids=["e1"])
        assert a.hash() == b.hash()

    def test_changes_with_ids(self):
        a = EdgeBinding(ids=["e1"])
        b = EdgeBinding(ids=["e2"])
        assert a.hash() != b.hash()

    def test_id_order_does_not_matter(self):
        # ids are hashed via frozenset.
        a = EdgeBinding(ids=["e1", "e2"])
        b = EdgeBinding(ids=["e2", "e1"])
        assert a.hash() == b.hash()
