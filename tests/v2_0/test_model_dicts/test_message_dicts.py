"""Parity tests for `MessageDictUtil`."""

from __future__ import annotations

import copy

import pytest

from translator_tom.v2_0.model_dicts.message import MessageDict, MessageDictUtil
from translator_tom.v2_0.models.analysis import Analysis
from translator_tom.v2_0.models.auxiliary_graph import AuxiliaryGraph
from translator_tom.v2_0.models.edge_binding import EdgeBinding
from translator_tom.v2_0.models.knowledge_graph import Edge, KnowledgeGraph, Node
from translator_tom.v2_0.models.message import Message
from translator_tom.v2_0.models.node_binding import NodeBinding
from translator_tom.v2_0.models.query_graph import QNode, QueryGraph
from translator_tom.v2_0.models.result import Result
from translator_tom.v2_0.models.retrieval_source import RetrievalSource


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
        knowledge_level="knowledge_assertion",
        agent_type="manual_agent",
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
                node_bindings={"n0": NodeBinding(ids=["CHEBI:1"])},
                analyses=[
                    Analysis(
                        resource_id="infores:x",
                        edge_bindings={"e0": EdgeBinding(ids=["kg0"])},
                    )
                ],
            )
        ],
        auxiliary_graphs={"a0": AuxiliaryGraph(edges=["kg0"])},
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
                    node_bindings={"n0": NodeBinding(ids=["DRUGBANK:2"])},
                    analyses=[Analysis(resource_id="infores:y")],
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
        m: MessageDict = {"query_graph": {"nodes": {"n0": {}}}}
        other: MessageDict = {"query_graph": {"nodes": {"n1": {}}}}
        with pytest.raises(NotImplementedError):
            MessageDictUtil.update(m, other)

    def test_update_isolates_denormalized_other(self):
        """A denormalized `other` (edges colliding on hash) is not mutated by the merge."""
        dup = Message.from_dict(
            {
                "knowledge_graph": {
                    "nodes": {},
                    "edges": {
                        "k1": {
                            "subject": "n0",
                            "object": "n1",
                            "predicate": "biolink:related_to",
                            "sources": [
                                {
                                    "resource_id": "ks",
                                    "resource_role": "primary_knowledge_source",
                                }
                            ],
                            "knowledge_level": "knowledge_assertion",
                            "agent_type": "manual_agent",
                            "attributes": [
                                {"attribute_type_id": "biolink:a", "value": 1}
                            ],
                        },
                        "k2": {
                            "subject": "n0",
                            "object": "n1",
                            "predicate": "biolink:related_to",
                            "sources": [
                                {
                                    "resource_id": "ks",
                                    "resource_role": "primary_knowledge_source",
                                }
                            ],
                            "knowledge_level": "knowledge_assertion",
                            "agent_type": "manual_agent",
                            "attributes": [
                                {"attribute_type_id": "biolink:b", "value": 2}
                            ],
                        },
                    },
                },
                "results": [],
            }
        ).to_dict()
        dup_before = copy.deepcopy(dup)
        MessageDictUtil.update({}, dup)
        assert dup == dup_before

    def test_update_does_not_mutate_or_alias_other(self):
        """MessageDictUtil.update must fully isolate `other` (parity with the model)."""

        def message_dict(tag: str, val: int) -> MessageDict:
            return Message.from_dict(
                {
                    "knowledge_graph": {
                        "nodes": {
                            "n0": {
                                "name": tag,
                                "categories": ["biolink:NamedThing"],
                                "attributes": [
                                    {"attribute_type_id": "biolink:x", "value": val}
                                ],
                            }
                        },
                        "edges": {
                            "shared": {
                                "subject": "n0",
                                "object": "n0",
                                "predicate": "biolink:related_to",
                                "sources": [
                                    {
                                        "resource_id": "ks",
                                        "resource_role": "primary_knowledge_source",
                                    }
                                ],
                                "knowledge_level": "knowledge_assertion",
                                "agent_type": "manual_agent",
                                "attributes": [
                                    {"attribute_type_id": "biolink:y", "value": val}
                                ],
                            },
                            f"e{tag}": {
                                "subject": "n0",
                                "object": "n0",
                                "predicate": "biolink:related_to",
                                "sources": [
                                    {
                                        "resource_id": f"ks{tag}",
                                        "resource_role": "primary_knowledge_source",
                                    }
                                ],
                                "knowledge_level": "knowledge_assertion",
                                "agent_type": "manual_agent",
                            },
                        },
                    },
                    "results": [
                        {
                            "node_bindings": {"n0": {"ids": ["n0"]}},
                            "analyses": [
                                {
                                    "resource_id": f"ara{tag}",
                                    "edge_bindings": {"e0": {"ids": ["shared"]}},
                                }
                            ],
                        }
                    ],
                    "auxiliary_graphs": {f"aux{tag}": {"edges": ["shared"]}},
                }
            ).to_dict()

        a = message_dict("A", 1)
        b = message_dict("B", 2)

        b_before = copy.deepcopy(b)
        MessageDictUtil.update(a, b)
        assert b == b_before  # other unmutated

        # Mutating everything reachable in `a` must not leak into `b`.
        b_snapshot = copy.deepcopy(b)
        for edge in a["knowledge_graph"]["edges"].values():
            edge["attributes"] = [{"attribute_type_id": "biolink:MUT", "value": 0}]
            edge["sources"][0]["resource_id"] = "MUT"
        for node in a["knowledge_graph"]["nodes"].values():
            node["name"] = "MUT"
        for result in a["results"]:
            result["analyses"] = []
        for graph in a["auxiliary_graphs"].values():
            graph["edges"] = ["MUT"]
        assert b == b_snapshot

    def test_merges_kg_and_auxiliary_graphs(self):
        # `other` carries a kg + aux (not just results) to exercise the
        # KnowledgeGraphDictUtil.update and merge_dictionaries branches.
        m = _message()
        other = Message(
            knowledge_graph=KnowledgeGraph(
                nodes={
                    "CHEBI:2": Node(
                        categories=["biolink:ChemicalEntity"], attributes=[]
                    )
                },
                edges={"kg1": _edge("CHEBI:2", "MONDO:2")},
            ),
            auxiliary_graphs={"a1": AuxiliaryGraph(edges=["kg1"])},
        )
        m_dict = m.to_dict()
        model_mapping = m.update(other)
        dict_mapping = MessageDictUtil.update(m_dict, other.to_dict())
        assert dict_mapping == model_mapping
        assert m_dict == m.to_dict()

    def test_query_graphs_equal_but_extra_key_do_not_raise(self):
        # Query graphs equal by hash but differing by an extra key: the model ignores
        # extras (hash-based `==`), so MessageDictUtil.update must not raise either.
        qg = QueryGraph(nodes={"n0": QNode()})
        qg_extra = QueryGraph(nodes={"n0": QNode()}, foo="bar")
        m = Message(query_graph=qg)
        other = Message(query_graph=qg_extra)
        m_dict = m.to_dict()
        m.update(other)
        MessageDictUtil.update(m_dict, other.to_dict())
        assert MessageDictUtil.hash(m_dict) == m.hash()
