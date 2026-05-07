"""Tests for translator_tom.models.message."""

import pytest
from pydantic import ValidationError

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
    QEdge,
    QNode,
    QueryGraph,
    Result,
    RetrievalSource,
)


def _src() -> RetrievalSource:
    return RetrievalSource(
        resource_id="infores:foo",
        resource_role="primary_knowledge_source",
    )


def _node() -> Node:
    return Node(name="x", categories=["biolink:NamedThing"], attributes=[])


def _edge(subject: str = "A:1", object_: str = "B:2") -> Edge:
    return Edge(
        predicate="biolink:related_to",
        subject=subject,
        object=object_,
        sources=[_src()],
    )


def _result(node_id: str = "A:1", edge_id: str = "e1") -> Result:
    return Result(
        node_bindings={"n0": [NodeBinding(id=node_id, attributes=[])]},
        analyses=[
            Analysis(
                resource_id="infores:test",
                edge_bindings={
                    "e0": [EdgeBinding(id=edge_id, attributes=[])]
                },
            )
        ],
    )


class TestMessageBasics:
    def test_default_construction(self):
        m = Message()
        assert m.results is None
        assert m.query_graph is None
        assert m.knowledge_graph is None
        assert m.auxiliary_graphs is None

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            Message(bogus="x")  # type: ignore[call-arg]


class TestMessageProperties:
    def test_results_list_when_none(self):
        assert Message().results_list == []

    def test_results_list_when_set(self):
        r = _result()
        assert Message(results=[r]).results_list == [r]

    def test_auxiliary_graphs_dict_when_none(self):
        assert Message().auxiliary_graphs_dict == {}

    def test_auxiliary_graphs_dict_when_set(self):
        d = {"g1": AuxiliaryGraph(edges=["e1"], attributes=[])}
        assert Message(auxiliary_graphs=d).auxiliary_graphs_dict == d


class TestMessageNormalize:
    def test_returns_empty_when_no_kg(self):
        assert Message().normalize() == {}

    def test_propagates_mapping_to_results_and_aux(self):
        # KG re-keys "old_e" → edge.hash(); the same mapping should be applied
        # to result edge bindings and aux graph edge lists.
        edge = _edge()
        kg = KnowledgeGraph(nodes={"A:1": _node()}, edges={"old_e": edge})
        m = Message(
            knowledge_graph=kg,
            results=[_result(edge_id="old_e")],
            auxiliary_graphs={"g1": AuxiliaryGraph(edges=["old_e"], attributes=[])},
        )
        mapping = m.normalize()
        new_id = edge.hash()
        assert mapping["old_e"] == new_id
        # aux graph edges remapped
        assert m.auxiliary_graphs is not None
        assert m.auxiliary_graphs["g1"].edges == [new_id]
        # result edge bindings remapped
        assert m.results is not None
        assert (
            m.results[0].analyses[0].edge_bindings["e0"][0].id  # type: ignore[union-attr]
            == new_id
        )


class TestMessagePruneKg:
    def test_no_op_when_no_kg(self):
        m = Message()
        m.prune_kg()  # should not raise
        assert m.knowledge_graph is None

    def test_delegates_to_kg_prune(self):
        kg = KnowledgeGraph(
            nodes={"A:1": _node(), "B:2": _node(), "A:99": _node()},
            edges={"e1": _edge()},
        )
        m = Message(
            knowledge_graph=kg,
            results=[_result(node_id="A:1", edge_id="e1")],
        )
        m.prune_kg()
        assert m.knowledge_graph is not None
        assert "A:99" not in m.knowledge_graph.nodes
        assert "A:1" in m.knowledge_graph.nodes


class TestMessageUpdate:
    def test_raises_when_query_graphs_differ(self):
        a = Message(query_graph=QueryGraph(nodes={}, edges={"q1": QEdge(subject="n1", object="n2")}))
        b = Message(query_graph=QueryGraph(nodes={"n1": QNode()}, edges={}))
        with pytest.raises(NotImplementedError):
            a.update(b)

    def test_assigns_kg_when_self_has_none(self):
        a = Message()
        b = Message(knowledge_graph=KnowledgeGraph.new())
        a.update(b, pre_normalized="both")
        assert a.knowledge_graph is not None

    def test_merges_kgs_when_both_present(self):
        a_edge = _edge(subject="A:1")
        b_edge = _edge(subject="A:9")
        a = Message(
            knowledge_graph=KnowledgeGraph(
                nodes={"A:1": _node()}, edges={a_edge.hash(): a_edge}
            )
        )
        b = Message(
            knowledge_graph=KnowledgeGraph(
                nodes={"A:9": _node()}, edges={b_edge.hash(): b_edge}
            )
        )
        a.update(b, pre_normalized="both")
        assert a.knowledge_graph is not None
        assert set(a.knowledge_graph.edges) == {a_edge.hash(), b_edge.hash()}

    def test_assigns_results_when_self_has_none(self):
        a = Message()
        b = Message(results=[_result()])
        a.update(b, pre_normalized="both")
        assert a.results is not None
        assert len(a.results) == 1

    def test_merges_results(self):
        a = Message(results=[_result(node_id="A:1")])
        b = Message(results=[_result(node_id="A:2")])
        a.update(b, pre_normalized="both")
        assert a.results is not None
        assert len(a.results) == 2

    def test_assigns_aux_graphs_when_self_has_none(self):
        a = Message()
        b = Message(
            auxiliary_graphs={"g1": AuxiliaryGraph(edges=["e1"], attributes=[])}
        )
        a.update(b, pre_normalized="both")
        assert a.auxiliary_graphs is not None
        assert "g1" in a.auxiliary_graphs

    def test_merges_aux_graphs(self):
        a = Message(
            auxiliary_graphs={"g1": AuxiliaryGraph(edges=["e1"], attributes=[])}
        )
        b = Message(
            auxiliary_graphs={"g2": AuxiliaryGraph(edges=["e2"], attributes=[])}
        )
        a.update(b, pre_normalized="both")
        assert a.auxiliary_graphs is not None
        assert set(a.auxiliary_graphs) == {"g1", "g2"}

    def test_does_not_mutate_other(self):
        # update deepcopies `other` before normalizing.
        edge = _edge()
        a = Message()
        b = Message(
            knowledge_graph=KnowledgeGraph(nodes={}, edges={"old": edge})
        )
        a.update(b, pre_normalized="self")  # forces other to be normalized
        assert "old" in b.knowledge_graph.edges  # type: ignore[union-attr]
