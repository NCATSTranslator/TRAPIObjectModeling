import pytest

from translator_tom import (
    Analysis,
    Attribute,
    AuxiliaryGraph,
    Edge,
    EdgeBinding,
    KnowledgeGraph,
    Message,
    Node,
    NodeBinding,
    QNode,
    Response,
    Result,
    RetrievalSource,
)
from translator_tom.v2_0.diff import Delta, diff


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
        knowledge_level="knowledge_assertion",
        agent_type="manual_agent",
    )


def _node(name: str = "Alice") -> Node:
    return Node(name=name, categories=["biolink:NamedThing"], attributes=[])


def _kinds(deltas: list[Delta]) -> set[tuple[tuple[str | int, ...], str]]:
    """(path, kind) pairs, for order-insensitive comparison."""
    return {(d.path, d.kind) for d in deltas}


# --- scalar / field-level behavior -------------------------------------------------


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
    assert diff(a, b) == [Delta(("value",), "changed", 1, 2)]


def test_none_vs_value_field():
    a = Attribute(attribute_type_id="biolink:foo", value=1)
    b = Attribute(attribute_type_id="biolink:foo", value=1, description="hi")
    (delta,) = diff(a, b)
    assert delta.path == ("description",)
    assert delta.kind == "changed"
    assert delta.left is None
    assert delta.right == "hi"


def test_multiple_field_differences():
    a = Attribute(attribute_type_id="biolink:foo", value=1)
    b = Attribute(attribute_type_id="biolink:bar", value=2)
    assert _kinds(diff(a, b)) == {
        (("attribute_type_id",), "changed"),
        (("value",), "changed"),
    }


# --- list alignment ----------------------------------------------------------------


def test_nested_list_changed_via_coarse_identity():
    """A same-type attribute whose value changed pairs by identity -> one `changed`."""
    a = Attribute(
        attribute_type_id="biolink:foo",
        value=1,
        attributes=[
            Attribute(attribute_type_id="biolink:sub", value="x"),
            Attribute(attribute_type_id="biolink:keep", value="k"),
        ],
    )
    b = Attribute(
        attribute_type_id="biolink:foo",
        value=1,
        attributes=[
            Attribute(attribute_type_id="biolink:sub", value="z"),
            Attribute(attribute_type_id="biolink:keep", value="k"),
        ],
    )
    assert diff(a, b) == [
        Delta(("attributes", "biolink:sub", "value"), "changed", "x", "z")
    ]


def test_list_length_difference_is_added():
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
            Attribute(attribute_type_id="biolink:other", value="y"),
        ],
    )
    (delta,) = diff(a, b)
    assert delta.path == ("attributes", "biolink:other")
    assert delta.kind == "added"
    assert delta.locator == "biolink:other"


def test_scalar_list_elements_equal_not_reported():
    a = Node(categories=["biolink:Gene", "biolink:NamedThing"], attributes=[])
    b = Node(categories=["biolink:Gene", "biolink:NamedThing"], attributes=[])
    assert diff(a, b) == []


def test_scalar_list_element_change_is_add_remove():
    """A changed scalar list member is a multiset add+remove, not a positional change."""
    a = Node(categories=["biolink:Gene", "biolink:NamedThing"], attributes=[])
    b = Node(categories=["biolink:Gene", "biolink:Protein"], attributes=[])
    assert _kinds(diff(a, b)) == {
        (("categories", "biolink:NamedThing"), "removed"),
        (("categories", "biolink:Protein"), "added"),
    }


def test_scalar_list_reorder_not_reported():
    """Scalar list order is meaningless in TRAPI -> no `reordered` delta."""
    a = Node(categories=["biolink:Gene", "biolink:Protein"], attributes=[])
    b = Node(categories=["biolink:Protein", "biolink:Gene"], attributes=[])
    assert diff(a, b) == []


# --- dict handling -----------------------------------------------------------------


def test_dict_key_only_in_one():
    kg_a = KnowledgeGraph(nodes={"A:1": _node()}, edges={})
    kg_b = KnowledgeGraph(nodes={"A:1": _node(), "A:2": _node(name="Bob")}, edges={})
    (delta,) = diff(kg_a, kg_b)
    assert delta.path == ("nodes", "A:2")
    assert delta.kind == "added"


def test_dict_value_difference():
    kg_a = KnowledgeGraph(nodes={}, edges={"e1": _edge(subject="A:1")})
    kg_b = KnowledgeGraph(nodes={}, edges={"e1": _edge(subject="A:9")})
    assert diff(kg_a, kg_b) == [
        Delta(("edges", "e1", "subject"), "changed", "A:1", "A:9")
    ]


def test_deeply_nested_path():
    kg_a = KnowledgeGraph(
        nodes={"A:1": _node(name="Alice")},
        edges={"e1": _edge(subject="A:1", object_="B:2")},
    )
    kg_b = KnowledgeGraph(
        nodes={"A:1": _node(name="Bob")},
        edges={"e1": _edge(subject="A:1", object_="B:9")},
    )
    assert _kinds(diff(kg_a, kg_b)) == {
        (("nodes", "A:1", "name"), "changed"),
        (("edges", "e1", "object"), "changed"),
    }


def test_nested_container_multiple_diffs():
    kg_a = KnowledgeGraph(
        nodes={"A:1": _node(name="Alice"), "A:2": _node(name="Bob")},
        edges={"e1": _edge(subject="A:1"), "e2": _edge(object_="B:2")},
    )
    kg_b = KnowledgeGraph(
        nodes={"A:1": _node(name="Alice"), "A:2": _node(name="Carol")},
        edges={"e1": _edge(subject="A:9"), "e2": _edge(object_="B:2")},
    )
    assert _kinds(diff(kg_a, kg_b)) == {
        (("nodes", "A:2", "name"), "changed"),
        (("edges", "e1", "subject"), "changed"),
    }


# --- strict vs identity (hash short-circuit) ---------------------------------------


def _edge_with_attr(value: int) -> Edge:
    return Edge(
        predicate="biolink:related_to",
        subject="A:1",
        object="B:2",
        sources=[_src()],
        knowledge_level="knowledge_assertion",
        agent_type="manual_agent",
        attributes=[Attribute(attribute_type_id="biolink:foo", value=value)],
    )


def test_identity_mode_short_circuits_on_equal_hash():
    """strict=False: equal .hash() short-circuits even if excluded fields differ."""
    edge_a, edge_b = _edge_with_attr(1), _edge_with_attr(2)
    assert edge_a.hash() == edge_b.hash()  # Edge.hash ignores attributes
    assert diff(edge_a, edge_b, strict=False) == []


def test_strict_descends_past_hash_equality():
    """strict=True finds the attribute change hidden behind an equal edge hash."""
    edge_a, edge_b = _edge_with_attr(1), _edge_with_attr(2)
    assert edge_a.hash() == edge_b.hash()
    assert diff(edge_a, edge_b) == [
        Delta(("attributes", "biolink:foo", "value"), "changed", 1, 2)
    ]


def test_descends_when_hash_differs():
    assert diff(_edge(subject="A:1"), _edge(subject="A:9")) == [
        Delta(("subject",), "changed", "A:1", "A:9")
    ]


# --- extra fields ------------------------------------------------------------------


def test_extra_field_differing_values_reported():
    a = QNode(categories=["biolink:Gene"], foo=1)
    b = QNode(categories=["biolink:Gene"], foo=2)
    (delta,) = diff(a, b)
    assert (delta.path, delta.kind, delta.left, delta.right) == (
        ("foo",),
        "changed",
        1,
        2,
    )


def test_extra_field_identical_values_still_reported():
    """Extras are opaque (never value-compared), so any extra key is reported as changed."""
    a = QNode(categories=["biolink:Gene"], foo=1)
    b = QNode(categories=["biolink:Gene"], foo=1)
    assert diff(a, b) == [Delta(("foo",), "changed", 1, 1, "QNode#" + a.hash()[:8])]


def test_extra_field_only_on_one_side_is_changed():
    a = QNode(categories=["biolink:Gene"], foo=1)
    b = QNode(categories=["biolink:Gene"])
    (delta,) = diff(a, b)
    assert delta.path == ("foo",)
    assert delta.kind == "changed"
    assert delta.left == 1
    assert delta.right is None


def test_forbid_extra_models_unaffected():
    assert diff(_edge(), _edge()) == []


# --- response-level scenarios ------------------------------------------------------


def _binding(edge_id: str) -> EdgeBinding:
    return EdgeBinding(ids=[edge_id])


def _result(node_id: str, edge_id: str, *, score: float = 0.9) -> Result:
    return Result(
        node_bindings={"n0": NodeBinding(ids=[node_id])},
        analyses=[
            Analysis(
                resource_id="infores:ara",
                score=score,
                edge_bindings={"e0": _binding(edge_id)},
            )
        ],
    )


def _message(edge_key: str, node_id: str = "A:1") -> Message:
    return Message(
        knowledge_graph=KnowledgeGraph(
            nodes={node_id: _node()}, edges={edge_key: _edge(subject=node_id)}
        ),
        results=[_result(node_id, edge_key)],
    )


def test_results_reorder_is_single_reordered_delta():
    r1 = _result("A:1", "e1")
    r2 = _result("A:2", "e2")
    a = Message(results=[r1, r2])
    b = Message(results=[r2, r1])
    (delta,) = diff(a, b)
    assert delta.path == ("results",)
    assert delta.kind == "reordered"


def test_score_change_structural_only():
    a = Message(results=[_result("A:1", "e1", score=0.9)])
    b = Message(results=[_result("A:1", "e1", score=0.7)])

    (delta,) = diff(a, b)  # structural
    assert delta.kind == "changed"
    assert delta.path[-1] == "score"
    assert (delta.left, delta.right) == (0.9, 0.7)

    assert diff(a, b, strict=False) == []  # identity: Result.hash ignores score


def test_arbitrary_edge_keys_matched_after_normalize():
    left = Response(message=_message("svcA:e1"))
    right = Response(message=_message("svcB:99"))

    # Without normalize the arbitrary KG edge keys look entirely different.
    assert diff(left, right) != []
    # With normalize both sides re-key edges by content hash and line up.
    assert diff(left, right, normalize=True) == []


def _aux_message(edge_key: str, aux_key: str) -> Message:
    return Message(
        knowledge_graph=KnowledgeGraph(
            nodes={"A:1": _node()}, edges={edge_key: _edge()}
        ),
        auxiliary_graphs={aux_key: AuxiliaryGraph(edges=[edge_key])},
    )


def test_aux_graphs_matched_by_content_after_normalize():
    left = _aux_message("svcA:e1", "aux1")
    right = _aux_message("svcB:99", "auxX")
    # Equivalent aux graphs under different dict keys align by content after normalize.
    assert diff(left, right, normalize=True) == []


def test_dropped_result_has_locator():
    a = Message(results=[_result("A:1", "e1"), _result("A:2", "e2")])
    b = Message(results=[_result("A:1", "e1")])
    (delta,) = diff(a, b)
    assert delta.kind == "removed"
    assert delta.locator == "n0=A:2"


def test_normalize_does_not_mutate_inputs():
    left = Response(message=_message("svcA:e1"))
    right = Response(message=_message("svcB:99"))
    diff(left, right, normalize=True)
    assert set(left.message.knowledge_graph.edges) == {"svcA:e1"}
    assert set(right.message.knowledge_graph.edges) == {"svcB:99"}


def test_normalize_raises_for_non_message_inputs():
    with pytest.raises(ValueError, match="requires Message or Response"):
        diff(_edge(), _edge(), normalize=True)
