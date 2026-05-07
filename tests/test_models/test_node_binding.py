"""Tests for translator_tom.models.node_binding."""

import pytest
from pydantic import ValidationError

from translator_tom import Attribute, NodeBinding


def _attr(value: int = 1) -> Attribute:
    return Attribute(attribute_type_id="biolink:foo", value=value)


class TestNodeBindingBasics:
    def test_required_fields(self):
        nb = NodeBinding(id="A:1", attributes=[])
        assert nb.id == "A:1"
        assert nb.query_id is None
        assert nb.attributes == []

    def test_id_required(self):
        with pytest.raises(ValidationError):
            NodeBinding(attributes=[])  # type: ignore[call-arg]

    def test_attributes_required(self):
        with pytest.raises(ValidationError):
            NodeBinding(id="A:1")  # type: ignore[call-arg]


class TestNodeBindingHash:
    def test_deterministic(self):
        a = NodeBinding(id="A:1", attributes=[_attr(1)])
        b = NodeBinding(id="A:1", attributes=[_attr(1)])
        assert a.hash() == b.hash()

    def test_changes_with_id(self):
        a = NodeBinding(id="A:1", attributes=[])
        b = NodeBinding(id="A:2", attributes=[])
        assert a.hash() != b.hash()

    def test_changes_with_query_id(self):
        a = NodeBinding(id="A:1", attributes=[])
        b = NodeBinding(id="A:1", query_id="Q:1", attributes=[])
        assert a.hash() != b.hash()

    def test_attribute_order_does_not_matter(self):
        a1 = _attr(1)
        a2 = _attr(2)
        a = NodeBinding(id="A:1", attributes=[a1, a2])
        b = NodeBinding(id="A:1", attributes=[a2, a1])
        assert a.hash() == b.hash()
