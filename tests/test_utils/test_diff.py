import pytest

from translator_tom import (
    Attribute,
    Edge,
    KnowledgeGraph,
    Node,
    RetrievalSource,
)
from translator_tom.utils.diff import diff


def _src() -> RetrievalSource:
    return RetrievalSource(
        resource_id="infores:foo",
        resource_role="primary_knowledge_source",
    )


def _edge(subject: str = "A:1", object_: str = "B:2") -> Edge:
    return Edge(
        predicate="biolink:related_to",
        subject=subject,
        object=object_,
        sources=[_src()],
    )


def _node(name: str = "Alice") -> Node:
    return Node(name=name, categories=["biolink:NamedThing"], attributes=[])


def test_identical_objects_returns_empty():
    a = Attribute(attribute_type_id="biolink:foo", value=1)
    b = Attribute(attribute_type_id="biolink:foo", value=1)
    assert diff(a, b) == []


def test_different_types_raises():
    with pytest.raises(ValueError, match="Cannot compare different object types"):
        diff(_node(), _edge())  # type: ignore[arg-type]


def test_primitive_field_difference():
    a = Attribute(attribute_type_id="biolink:foo", value=1)
    b = Attribute(attribute_type_id="biolink:foo", value=2)
    assert diff(a, b) == [("value",)]


def test_none_vs_value_field():
    a = Attribute(attribute_type_id="biolink:foo", value=1)
    b = Attribute(attribute_type_id="biolink:foo", value=1, description="hi")
    assert diff(a, b) == [("description",)]


def test_multiple_field_differences():
    a = Attribute(attribute_type_id="biolink:foo", value=1)
    b = Attribute(attribute_type_id="biolink:bar", value=2)
    paths = set(diff(a, b))
    assert paths == {("attribute_type_id",), ("value",)}


def test_nested_list_element_difference():
    a = Attribute(
        attribute_type_id="biolink:foo",
        value=1,
        attributes=[
            Attribute(attribute_type_id="biolink:sub", value="x"),
            Attribute(attribute_type_id="biolink:sub", value="y"),
        ],
    )
    b = Attribute(
        attribute_type_id="biolink:foo",
        value=1,
        attributes=[
            Attribute(attribute_type_id="biolink:sub", value="x"),
            Attribute(attribute_type_id="biolink:sub", value="z"),
        ],
    )
    assert diff(a, b) == [("attributes", 1, "value")]


def test_list_length_difference():
    a = Attribute(
        attribute_type_id="biolink:foo",
        value=1,
        attributes=[Attribute(attribute_type_id="biolink:sub", value="x")],
    )
    b = Attribute(
        attribute_type_id="biolink:foo",
        value=1,
        attributes=[
            Attribute(attribute_type_id="biolink:sub", value="x"),
            Attribute(attribute_type_id="biolink:sub", value="y"),
        ],
    )
    assert diff(a, b) == [("attributes", 1)]


def test_dict_key_only_in_one():
    kg_a = KnowledgeGraph(nodes={"A:1": _node()}, edges={})
    kg_b = KnowledgeGraph(
        nodes={"A:1": _node(), "A:2": _node(name="Bob")}, edges={}
    )
    assert diff(kg_a, kg_b) == [("nodes", "A:2")]


def test_dict_value_difference():
    kg_a = KnowledgeGraph(nodes={}, edges={"e1": _edge(subject="A:1")})
    kg_b = KnowledgeGraph(nodes={}, edges={"e1": _edge(subject="A:9")})
    assert diff(kg_a, kg_b) == [("edges", "e1", "subject")]


def test_deeply_nested_path():
    kg_a = KnowledgeGraph(
        nodes={"A:1": _node(name="Alice")},
        edges={"e1": _edge(subject="A:1", object_="B:2")},
    )
    kg_b = KnowledgeGraph(
        nodes={"A:1": _node(name="Bob")},
        edges={"e1": _edge(subject="A:1", object_="B:9")},
    )
    paths = set(diff(kg_a, kg_b))
    assert paths == {("nodes", "A:1", "name"), ("edges", "e1", "object")}


def test_uses_hash_short_circuit_when_not_strict():
    """When strict=False, equal .hash() short-circuits even if fields differ."""
    # Edge.hash() ignores attributes, so two edges differing only in attributes
    # share a hash and diff(strict=False) will not descend into them.
    edge_a = Edge(
        predicate="biolink:related_to",
        subject="A:1",
        object="B:2",
        sources=[_src()],
        attributes=[Attribute(attribute_type_id="biolink:foo", value=1)],
    )
    edge_b = Edge(
        predicate="biolink:related_to",
        subject="A:1",
        object="B:2",
        sources=[_src()],
        attributes=[Attribute(attribute_type_id="biolink:foo", value=2)],
    )
    assert edge_a.hash() == edge_b.hash()
    assert diff(edge_a, edge_b, strict=False) == []


def test_strict_descends_past_hash_equality():
    """strict=True (default) ignores .hash() and finds field-level differences."""
    edge_a = Edge(
        predicate="biolink:related_to",
        subject="A:1",
        object="B:2",
        sources=[_src()],
        attributes=[Attribute(attribute_type_id="biolink:foo", value=1)],
    )
    edge_b = Edge(
        predicate="biolink:related_to",
        subject="A:1",
        object="B:2",
        sources=[_src()],
        attributes=[Attribute(attribute_type_id="biolink:foo", value=2)],
    )
    assert edge_a.hash() == edge_b.hash()
    assert diff(edge_a, edge_b) == [("attributes", 0, "value")]


def test_descends_when_hash_differs():
    """When .hash() differs, diff descends and captures field-level paths."""
    edge_a = _edge(subject="A:1")
    edge_b = _edge(subject="A:9")
    assert edge_a.hash() != edge_b.hash()
    assert diff(edge_a, edge_b) == [("subject",)]
