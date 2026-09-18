"""Tests for Message.solve_set_interpretation (v1_6 model layer).

TRAPI 1.6 uses a list of NodeBindings per QNode and has no COLLATE mode.
"""

import pytest

from translator_tom.v1_6 import (
    Analysis,
    EdgeBinding,
    KnowledgeGraph,
    Message,
    Node,
    NodeBinding,
    QEdge,
    QNode,
    QueryGraph,
    Result,
)


def _kg(*ids: str) -> KnowledgeGraph:
    return KnowledgeGraph(
        nodes={i: Node(categories=["biolink:NamedThing"], attributes=[]) for i in ids},
        edges={},
    )


def _result(node_bindings: dict[str, str], edge_bindings: dict[str, str]) -> Result:
    return Result(
        node_bindings={
            q: [NodeBinding(id=v, attributes=[])] for q, v in node_bindings.items()
        },
        analyses=[
            Analysis(
                resource_id="infores:test",
                edge_bindings={
                    q: [EdgeBinding(id=e, attributes=[])] for q, e in edge_bindings.items()
                },
            )
        ],
    )


def _bindings(message: Message) -> list[dict[str, list[str]]]:
    return [
        {q: sorted(b.id for b in bs) for q, bs in r.node_bindings.items()}
        for r in message.results
    ]


def _edge(subject: str, obj: str) -> QEdge:
    return QEdge(subject=subject, object=obj, predicates=["biolink:related_to"])


def test_batch_passthrough():
    qg = QueryGraph(
        nodes={"A": QNode(ids=["A1"]), "B": QNode(categories=["biolink:Gene"])},
        edges={"e0": _edge("A", "B")},
    )
    m = Message(
        query_graph=qg,
        knowledge_graph=_kg("A1", "B1", "B2"),
        results=[
            _result({"A": "A1", "B": "B1"}, {"e0": "k1"}),
            _result({"A": "A1", "B": "B2"}, {"e0": "k2"}),
        ],
    )
    m.solve_set_interpretation()
    assert len(m.results) == 2


def test_all_binds_set_node_and_drops_incomplete():
    qg = QueryGraph(
        nodes={
            "A": QNode(ids=["A1"]),
            "B": QNode(set_interpretation="ALL", ids=["BSET"], member_ids=["B1", "B2"]),
        },
        edges={"e0": _edge("A", "B")},
    )
    m = Message(
        query_graph=qg,
        knowledge_graph=_kg("A1", "A2", "B1", "B2", "BSET"),
        results=[
            _result({"A": "A1", "B": "B1"}, {"e0": "k1"}),
            _result({"A": "A1", "B": "B2"}, {"e0": "k2"}),
            _result({"A": "A2", "B": "B1"}, {"e0": "k3"}),  # A2 lacks B2
        ],
    )
    m.solve_set_interpretation()
    assert _bindings(m) == [{"A": ["A1"], "B": ["BSET"]}]


def test_all_all_cross_edges():
    qg = QueryGraph(
        nodes={
            "A": QNode(set_interpretation="ALL", ids=["ASET"], member_ids=["A1", "A2"]),
            "B": QNode(set_interpretation="ALL", ids=["BSET"], member_ids=["B1", "B2"]),
        },
        edges={"e0": _edge("A", "B")},
    )
    m = Message(
        query_graph=qg,
        knowledge_graph=_kg("A1", "A2", "B1", "B2", "ASET", "BSET"),
        results=[
            _result({"A": "A1", "B": "B1"}, {"e0": "k1"}),
            _result({"A": "A2", "B": "B2"}, {"e0": "k2"}),
        ],
    )
    m.solve_set_interpretation()
    assert _bindings(m) == [{"A": ["ASET"], "B": ["BSET"]}]


def test_all_all_missing_member_no_results():
    qg = QueryGraph(
        nodes={
            "A": QNode(set_interpretation="ALL", ids=["ASET"], member_ids=["A1", "A2"]),
            "B": QNode(set_interpretation="ALL", ids=["BSET"], member_ids=["B1", "B2"]),
        },
        edges={"e0": _edge("A", "B")},
    )
    m = Message(
        query_graph=qg,
        knowledge_graph=_kg("A1", "A2", "B1", "B2", "ASET", "BSET"),
        results=[_result({"A": "A1", "B": "B1"}, {"e0": "k1"})],
    )
    m.solve_set_interpretation()
    assert len(m.results) == 0


def test_missing_member_node_raises():
    qg = QueryGraph(
        nodes={
            "A": QNode(ids=["A1"]),
            "B": QNode(set_interpretation="ALL", ids=["BSET"], member_ids=["B1"]),
        },
        edges={"e0": _edge("A", "B")},
    )
    m = Message(
        query_graph=qg,
        knowledge_graph=_kg("A1", "B1"),  # BSET absent
        results=[_result({"A": "A1", "B": "B1"}, {"e0": "k1"})],
    )
    with pytest.raises(ValueError, match="member node"):
        m.solve_set_interpretation()


def test_many_raises_and_skip():
    qg = QueryGraph(
        nodes={"A": QNode(ids=["A1"]), "B": QNode(set_interpretation="MANY", ids=["B1", "B2"])},
        edges={"e0": _edge("A", "B")},
    )
    m = Message(
        query_graph=qg,
        knowledge_graph=_kg("A1", "B1", "B2"),
        results=[
            _result({"A": "A1", "B": "B1"}, {"e0": "k1"}),
            _result({"A": "A1", "B": "B2"}, {"e0": "k2"}),
        ],
    )
    with pytest.raises(ValueError, match="MANY"):
        m.solve_set_interpretation()
    m.solve_set_interpretation(skip_many=True)
    assert len(m.results) == 2


def test_no_results_noop():
    qg = QueryGraph(
        nodes={"A": QNode(categories=["biolink:Gene"])}, edges={"e0": _edge("A", "A")}
    )
    m = Message(query_graph=qg)
    m.solve_set_interpretation()
    assert m.results is None
