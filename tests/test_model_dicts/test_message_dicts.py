"""Parity tests for `MessageDictUtil`."""

from __future__ import annotations

import pytest

from translator_tom.model_dicts.message import MessageDict, MessageDictUtil
from translator_tom.models.analysis import Analysis
from translator_tom.models.auxiliary_graph import AuxiliaryGraph
from translator_tom.models.edge_binding import EdgeBinding
from translator_tom.models.knowledge_graph import Edge, KnowledgeGraph, Node
from translator_tom.models.message import Message
from translator_tom.models.node_binding import NodeBinding
from translator_tom.models.query_graph import QNode, QueryGraph
from translator_tom.models.result import Result
from translator_tom.models.retrieval_source import RetrievalSource


def _edge(subject: str, obj: str) -> Edge:
    return Edge(
        predicate="biolink:treats",
        subject=subject,
        object=obj,
        sources=[
            RetrievalSource(
                resource_id="infores:x", resource_role="primary_knowledge_source"
            )
        ],
    )


def _message() -> Message:
    return Message(
        knowledge_graph=KnowledgeGraph(
            nodes={
                "CHEBI:1": Node(categories=["biolink:ChemicalEntity"], attributes=[]),
                "MONDO:1": Node(categories=["biolink:Disease"], attributes=[]),
            },
            edges={"kg0": _edge("CHEBI:1", "MONDO:1")},
        ),
        results=[
            Result(
                node_bindings={"n0": [NodeBinding(id="CHEBI:1", attributes=[])]},
                analyses=[
                    Analysis(
                        resource_id="infores:x",
                        edge_bindings={"e0": [EdgeBinding(id="kg0", attributes=[])]},
                    )
                ],
            )
        ],
        auxiliary_graphs={"a0": AuxiliaryGraph(edges=["kg0"], attributes=[])},
    )


class TestListAccessors:
    def test_results_list(self):
        m = _message()
        assert len(MessageDictUtil.results_list(m.to_dict())) == 1
        assert MessageDictUtil.results_list({}) == []

    def test_auxiliary_graphs_dict(self):
        m = _message()
        assert set(MessageDictUtil.auxiliary_graphs_dict(m.to_dict())) == {"a0"}
        assert MessageDictUtil.auxiliary_graphs_dict({}) == {}


class TestHashParity:
    def test_full_message(self):
        m = _message()
        assert MessageDictUtil.hash(m.to_dict()) == m.hash()


class TestNormalize:
    def test_parity(self):
        m = _message()
        m_dict = m.to_dict()
        model_mapping = m.normalize()
        dict_mapping = MessageDictUtil.normalize(m_dict)
        assert dict_mapping == model_mapping
        assert m_dict == m.to_dict()


class TestPruneKg:
    def test_parity(self):
        m = _message()
        # Add an unused node/edge that pruning should drop.
        assert m.knowledge_graph is not None
        m.knowledge_graph.nodes["ORPHAN:1"] = Node(
            categories=["biolink:Gene"], attributes=[]
        )
        m.knowledge_graph.edges["orphan"] = _edge("ORPHAN:1", "ORPHAN:2")
        m_dict = m.to_dict()
        m.prune_kg()
        MessageDictUtil.prune_kg(m_dict)
        assert m_dict == m.to_dict()

    def test_none_kg_is_noop(self):
        message: MessageDict = {}
        MessageDictUtil.prune_kg(message)
        assert message == {}


class TestUpdate:
    def test_merges_and_hash_parity(self):
        m = _message()
        other = Message(
            results=[
                Result(
                    node_bindings={"n0": [NodeBinding(id="DRUGBANK:2", attributes=[])]},
                    analyses=[Analysis(resource_id="infores:y", edge_bindings={})],
                )
            ],
        )
        m_dict = m.to_dict()
        model_mapping = m.update(other)
        dict_mapping = MessageDictUtil.update(m_dict, other.to_dict())
        assert dict_mapping == model_mapping
        # Message.hash covers kg/results(node-bindings)/aux, robust to analysis ordering.
        assert MessageDictUtil.hash(m_dict) == m.hash()
        assert len(MessageDictUtil.results_list(m_dict)) == len(m.results_list)

    def test_mismatched_query_graph_raises(self):
        m: MessageDict = {"query_graph": {"nodes": {"n0": {}}, "edges": {}}}
        other: MessageDict = {"query_graph": {"nodes": {"n1": {}}, "edges": {}}}
        with pytest.raises(NotImplementedError):
            MessageDictUtil.update(m, other)

    def test_merges_kg_and_auxiliary_graphs(self):
        # `other` carries a kg + aux (not just results) to exercise the
        # KnowledgeGraphDictUtil.update and merge_dictionaries branches.
        m = _message()
        other = Message(
            knowledge_graph=KnowledgeGraph(
                nodes={
                    "CHEBI:2": Node(categories=["biolink:ChemicalEntity"], attributes=[])
                },
                edges={"kg1": _edge("CHEBI:2", "MONDO:2")},
            ),
            auxiliary_graphs={"a1": AuxiliaryGraph(edges=["kg1"], attributes=[])},
        )
        m_dict = m.to_dict()
        model_mapping = m.update(other)
        dict_mapping = MessageDictUtil.update(m_dict, other.to_dict())
        assert dict_mapping == model_mapping
        assert m_dict == m.to_dict()

    def test_query_graphs_equal_but_extra_key_do_not_raise(self):
        # Query graphs equal by hash but differing by an extra key: the model ignores
        # extras (hash-based `==`), so MessageDictUtil.update must not raise either.
        qg = QueryGraph(nodes={"n0": QNode()}, edges={})
        qg_extra = QueryGraph(nodes={"n0": QNode()}, edges={}, foo="bar")
        m = Message(query_graph=qg)
        other = Message(query_graph=qg_extra)
        m_dict = m.to_dict()
        m.update(other)
        MessageDictUtil.update(m_dict, other.to_dict())
        assert MessageDictUtil.hash(m_dict) == m.hash()
