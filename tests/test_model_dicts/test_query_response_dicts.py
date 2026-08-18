"""Parity tests for `QueryDictUtil` and `ResponseDictUtil`.

The hash-parity tests here exercise the full base-hash recursion chain: the tagged
`workflow` Operation union, the structural runner/fill-parameter unions, the
nested `query_graph`, and every nested model's hash override.
"""

from __future__ import annotations

from translator_tom.model_dicts.query import QueryDictUtil
from translator_tom.model_dicts.response import ResponseDictUtil
from translator_tom.models.analysis import Analysis
from translator_tom.models.edge_binding import EdgeBinding
from translator_tom.models.knowledge_graph import Edge, KnowledgeGraph, Node
from translator_tom.models.message import Message
from translator_tom.models.node_binding import NodeBinding
from translator_tom.models.query import Query
from translator_tom.models.query_graph import QEdge, QNode, QueryGraph
from translator_tom.models.response import Response
from translator_tom.models.result import Result
from translator_tom.models.retrieval_source import RetrievalSource
from translator_tom.models.workflow_operations import (
    DenyList,
    FillAllowListParameters,
    OperationFill,
    OperationScore,
)


def _full_message() -> Message:
    return Message(
        query_graph=QueryGraph(
            nodes={"n0": QNode(ids=["CHEBI:1"])},
            edges={
                "e0": QEdge(subject="n0", object="n1", predicates=["biolink:treats"])
            },
        ),
        knowledge_graph=KnowledgeGraph(
            nodes={
                "CHEBI:1": Node(categories=["biolink:ChemicalEntity"], attributes=[])
            },
            edges={
                "kg0": Edge(
                    predicate="biolink:treats",
                    subject="CHEBI:1",
                    object="MONDO:1",
                    sources=[
                        RetrievalSource(
                            resource_id="infores:x",
                            resource_role="primary_knowledge_source",
                        )
                    ],
                    knowledge_level="knowledge_assertion",
                    agent_type="manual_agent",
                )
            },
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
    )


def _workflow() -> list:
    return [
        OperationFill(
            id="fill",
            parameters=FillAllowListParameters(
                allowlist=["infores:a"], qedge_keys=["e0"]
            ),
        ),
        OperationScore(id="score", runner_parameters=DenyList(denylist=["infores:b"])),
    ]


class TestQuery:
    def test_workflow_list(self):
        q = Query(message=Message(), workflow=_workflow())
        assert QueryDictUtil.workflow_list(q.to_dict()) == q.to_dict()["workflow"]
        assert QueryDictUtil.workflow_list({"message": {}}) == []

    def test_new(self):
        assert QueryDictUtil.new() == Query.new().to_dict()

    def test_hash_parity_full_chain(self):
        q = Query(message=_full_message(), workflow=_workflow())
        assert QueryDictUtil.hash(q.to_dict()) == q.hash()


class TestResponse:
    def test_workflow_list(self):
        r = Response(message=Message(), workflow=_workflow())
        assert ResponseDictUtil.workflow_list(r.to_dict()) == r.to_dict()["workflow"]

    def test_new(self):
        assert ResponseDictUtil.new() == Response.new().to_dict()

    def test_hash_parity_full_chain(self):
        r = Response(message=_full_message(), workflow=_workflow())
        assert ResponseDictUtil.hash(r.to_dict()) == r.hash()
