"""Tests for translator_tom.v2_0.models.node_binding."""

import pytest
from pydantic import ValidationError

from translator_tom import NodeBinding


class TestNodeBindingBasics:
    def test_required_fields(self):
        nb = NodeBinding(ids=["A:1"])
        assert nb.ids == ["A:1"]

    def test_ids_required(self):
        with pytest.raises(ValidationError):
            NodeBinding()  # type: ignore[call-arg]

    def test_ids_min_length(self):
        with pytest.raises(ValidationError):
            NodeBinding(ids=[])


class TestNodeBindingHash:
    def test_deterministic(self):
        a = NodeBinding(ids=["A:1"])
        b = NodeBinding(ids=["A:1"])
        assert a.hash() == b.hash()

    def test_changes_with_ids(self):
        a = NodeBinding(ids=["A:1"])
        b = NodeBinding(ids=["A:2"])
        assert a.hash() != b.hash()

    def test_id_order_does_not_matter(self):
        # ids are hashed via frozenset.
        a = NodeBinding(ids=["A:1", "A:2"])
        b = NodeBinding(ids=["A:2", "A:1"])
        assert a.hash() == b.hash()
