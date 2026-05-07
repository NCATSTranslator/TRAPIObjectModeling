"""Tests for translator_tom.models.edge_binding."""

import pytest
from pydantic import ValidationError

from translator_tom import Attribute, EdgeBinding


def _attr(value: int = 1) -> Attribute:
    return Attribute(attribute_type_id="biolink:foo", value=value)


class TestEdgeBindingConstruction:
    def test_required_fields(self):
        eb = EdgeBinding(id="e1", attributes=[])
        assert eb.id == "e1"
        assert eb.attributes == []

    def test_id_required(self):
        with pytest.raises(ValidationError):
            EdgeBinding(attributes=[])  # type: ignore[call-arg]

    def test_attributes_required(self):
        with pytest.raises(ValidationError):
            EdgeBinding(id="e1")  # type: ignore[call-arg]


class TestEdgeBindingHash:
    def test_deterministic(self):
        a = EdgeBinding(id="e1", attributes=[_attr(1)])
        b = EdgeBinding(id="e1", attributes=[_attr(1)])
        assert a.hash() == b.hash()

    def test_changes_with_id(self):
        a = EdgeBinding(id="e1", attributes=[])
        b = EdgeBinding(id="e2", attributes=[])
        assert a.hash() != b.hash()

    def test_changes_with_attributes(self):
        a = EdgeBinding(id="e1", attributes=[_attr(1)])
        b = EdgeBinding(id="e1", attributes=[_attr(2)])
        assert a.hash() != b.hash()

    def test_attribute_order_does_not_matter(self):
        # Attributes are hashed via frozenset.
        a1 = _attr(1)
        a2 = _attr(2)
        a = EdgeBinding(id="e1", attributes=[a1, a2])
        b = EdgeBinding(id="e1", attributes=[a2, a1])
        assert a.hash() == b.hash()
