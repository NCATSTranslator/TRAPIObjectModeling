"""Parity tests for the knowledge-graph `*DictUtil` classes."""

from __future__ import annotations

import pytest

from translator_tom.v1_6.model_dicts.knowledge_graph import (
    EdgeDictUtil,
    KnowledgeGraphDictUtil,
    NodeDictUtil,
)
from translator_tom.v1_6.models.analysis import Analysis
from translator_tom.v1_6.models.attribute import Attribute, AttributeConstraint
from translator_tom.v1_6.models.auxiliary_graph import AuxiliaryGraph
from translator_tom.v1_6.models.edge_binding import EdgeBinding
from translator_tom.v1_6.models.knowledge_graph import Edge, KnowledgeGraph, Node
from translator_tom.v1_6.models.node_binding import NodeBinding
from translator_tom.v1_6.models.result import Result
from translator_tom.v1_6.models.retrieval_source import RetrievalSource


def _source(
    role: str = "primary_knowledge_source",
    rid: str = "infores:p",
    upstream: list[str] | None = None,
) -> RetrievalSource:
    return RetrievalSource(
        resource_id=rid,
        resource_role=role,  # type: ignore[arg-type]
        upstream_resource_ids=upstream,
    )


def _edge(subject: str, obj: str, **kw: object) -> Edge:
    kw.setdefault("sources", [_source()])
    return Edge(predicate="biolink:related_to", subject=subject, object=obj, **kw)  # type: ignore[arg-type]


def _node(*categories: str, attributes: list[Attribute] | None = None, **kw: object) -> Node:
    return Node(
        categories=list(categories) or ["biolink:NamedThing"],
        attributes=attributes or [],
        **kw,  # type: ignore[arg-type]
    )


# ============================================================================
# Node
# ============================================================================


class TestNode:
    def test_hash_parity(self):
        node = _node("biolink:Gene", name="BRCA1", is_set=False)
        assert NodeDictUtil.hash(node.to_dict()) == node.hash()

    def test_hash_ignores_categories_and_attributes(self):
        a = _node("biolink:Gene", name="X")
        b = _node(
            "biolink:Disease",
            name="X",
            attributes=[Attribute(attribute_type_id="biolink:z", value=1)],
        )
        assert NodeDictUtil.hash(a.to_dict()) == NodeDictUtil.hash(b.to_dict())

    def test_meets_constraints_parity(self):
        node = _node(
            "biolink:Gene",
            attributes=[Attribute(attribute_type_id="biolink:foo", value=1)],
        )
        constraints = [
            AttributeConstraint(id="biolink:foo", name="Foo", operator="==", value=1)
        ]
        assert NodeDictUtil.meets_constraints(
            node.to_dict(), [c.to_dict() for c in constraints]
        ) == node.meets_constraints(constraints)

    def test_update_parity(self):
        node = _node(
            "biolink:Gene",
            name=None,
            attributes=[Attribute(attribute_type_id="biolink:a", value=1)],
        )
        other = _node(
            "biolink:Disease",
            name="Named",
            attributes=[Attribute(attribute_type_id="biolink:b", value=2)],
        )
        node_dict = node.to_dict()
        node.update(other)
        NodeDictUtil.update(node_dict, other.to_dict())
        assert node_dict == node.to_dict()


# ============================================================================
# Edge
# ============================================================================


class TestEdge:
    def test_list_accessors(self):
        edge = _edge("n0", "n1")
        assert EdgeDictUtil.attributes_list(edge.to_dict()) == []
        assert EdgeDictUtil.qualifiers_list(edge.to_dict()) == []

    def test_hash_parity(self):
        edge = _edge("n0", "n1")
        assert EdgeDictUtil.hash(edge.to_dict()) == edge.hash()

    def test_primary_knowledge_source_parity(self):
        edge = _edge(
            "n0",
            "n1",
            sources=[
                _source(role="aggregator_knowledge_source", rid="infores:a"),
                _source(rid="infores:p"),
            ],
        )
        assert (
            EdgeDictUtil.primary_knowledge_source(edge.to_dict())
            == edge.primary_knowledge_source.to_dict()
        )

    def test_primary_knowledge_source_raises(self):
        edge = _edge(
            "n0", "n1", sources=[_source(role="aggregator_knowledge_source")]
        )
        with pytest.raises(ValueError, match="no .*primary_knowledge_source"):
            EdgeDictUtil.primary_knowledge_source(edge.to_dict())

    def test_last_downstream_source_parity(self):
        edge = _edge(
            "n0",
            "n1",
            sources=[
                _source(rid="infores:p"),
                _source(
                    role="aggregator_knowledge_source",
                    rid="infores:a",
                    upstream=["infores:p"],
                ),
            ],
        )
        result = EdgeDictUtil.last_downstream_source(edge.to_dict())
        expected = edge.last_downstream_source
        assert result == (expected.to_dict() if expected is not None else None)

    def test_is_self_edge_parity(self):
        assert EdgeDictUtil.is_self_edge(_edge("n0", "n0").to_dict()) is True
        assert EdgeDictUtil.is_self_edge(_edge("n0", "n1").to_dict()) is False

    def test_support_graphs_parity(self):
        edge = _edge(
            "n0",
            "n1",
            attributes=[
                Attribute(
                    attribute_type_id="biolink:support_graphs", value=["a0", "a1"]
                )
            ],
        )
        assert EdgeDictUtil.support_graphs(edge.to_dict()) == edge.support_graphs

    def test_update_parity(self):
        edge = _edge(
            "n0",
            "n1",
            attributes=[Attribute(attribute_type_id="biolink:a", value=1)],
        )
        other = _edge(
            "n0",
            "n1",
            attributes=[Attribute(attribute_type_id="biolink:b", value=2)],
            sources=[_source(role="aggregator_knowledge_source", rid="infores:a2")],
        )
        edge_dict = edge.to_dict()
        edge.update(other)
        EdgeDictUtil.update(edge_dict, other.to_dict())
        assert edge_dict == edge.to_dict()

    def test_meets_attribute_constraints_parity(self):
        edge = _edge(
            "n0",
            "n1",
            attributes=[Attribute(attribute_type_id="biolink:foo", value=5)],
        )
        constraints = [
            AttributeConstraint(id="biolink:foo", name="Foo", operator=">", value=1)
        ]
        assert EdgeDictUtil.meets_attribute_constraints(
            edge.to_dict(), [c.to_dict() for c in constraints]
        ) == edge.meets_attribute_constraints(constraints)

    def test_append_aggregator_parity(self):
        edge = _edge("n0", "n1", sources=[_source(rid="infores:p")])
        edge_dict = edge.to_dict()
        edge.append_aggregator("infores:agg")
        EdgeDictUtil.append_aggregator(edge_dict, "infores:agg")
        assert edge_dict["sources"] == edge.to_dict()["sources"]


# ============================================================================
# KnowledgeGraph
# ============================================================================


class TestKnowledgeGraph:
    def test_new(self):
        assert KnowledgeGraphDictUtil.new() == KnowledgeGraph.new().to_dict()
        assert KnowledgeGraphDictUtil.new() == {"nodes": {}, "edges": {}}

    def test_normalize_parity(self):
        kg = KnowledgeGraph(
            nodes={"n0": _node("biolink:Gene")},
            edges={"e0": _edge("n0", "n1")},
        )
        kg_dict = kg.to_dict()
        model_mapping = kg.normalize()
        dict_mapping = KnowledgeGraphDictUtil.normalize(kg_dict)
        assert dict_mapping == model_mapping
        assert kg_dict == kg.to_dict()

    def test_update_parity(self):
        kg = KnowledgeGraph(
            nodes={"n0": _node("biolink:Gene", name="A")},
            edges={"e0": _edge("n0", "n1")},
        )
        other = KnowledgeGraph(
            nodes={"n2": _node("biolink:Disease")},
            edges={"e1": _edge("n2", "n3")},
        )
        kg_dict = kg.to_dict()
        model_mapping = kg.update(other)
        dict_mapping = KnowledgeGraphDictUtil.update(kg_dict, other.to_dict())
        assert dict_mapping == model_mapping
        assert kg_dict == kg.to_dict()

    def test_prune_parity(self):
        kg = KnowledgeGraph(
            nodes={
                "n0": _node("biolink:Gene"),
                "n1": _node("biolink:Gene"),
                "n2": _node("biolink:Gene"),  # unused
            },
            edges={
                "e0": _edge("n0", "n1"),
                "e1": _edge("n1", "n2"),  # unused
            },
        )
        result = Result(
            node_bindings={"qn0": [NodeBinding(id="n0", attributes=[])]},
            analyses=[
                Analysis(
                    resource_id="infores:x",
                    edge_bindings={"qe0": [EdgeBinding(id="e0", attributes=[])]},
                )
            ],
        )
        aux_graphs: dict[str, AuxiliaryGraph] = {}
        kg_dict = kg.to_dict()
        kg.prune(aux_graphs, [result])
        KnowledgeGraphDictUtil.prune(kg_dict, {}, [result.to_dict()])
        assert kg_dict == kg.to_dict()


class TestEdgeUpdateBranches:
    """The subtle Edge.update branches: overlapping-source upstream roll-up + KL/AT skip."""

    def test_merges_overlapping_source_upstreams(self):
        # same (resource_id, role) -> same source hash -> upstreams rolled up (set union)
        edge = _edge(
            "n0", "n1", sources=[_source(rid="infores:p", upstream=["infores:a"])]
        )
        other = _edge(
            "n0", "n1", sources=[_source(rid="infores:p", upstream=["infores:b"])]
        )
        edge_dict = edge.to_dict()
        edge.update(other)
        EdgeDictUtil.update(edge_dict, other.to_dict())
        dict_up = {
            s["resource_id"]: set(s.get("upstream_resource_ids") or [])
            for s in edge_dict["sources"]
        }
        model_up = {
            s.resource_id: set(s.upstream_resource_ids or []) for s in edge.sources
        }
        assert dict_up == model_up
        assert dict_up["infores:p"] == {"infores:a", "infores:b"}

    def test_update_skips_knowledge_level_and_agent_type(self):
        edge = _edge(
            "n0", "n1", attributes=[Attribute(attribute_type_id="biolink:a", value=1)]
        )
        other = _edge(
            "n0",
            "n1",
            attributes=[
                Attribute(attribute_type_id="biolink:knowledge_level", value="ka"),
                Attribute(attribute_type_id="biolink:agent_type", value="manual"),
                Attribute(attribute_type_id="biolink:b", value=2),
            ],
        )
        edge_dict = edge.to_dict()
        edge.update(other)
        EdgeDictUtil.update(edge_dict, other.to_dict())
        assert edge_dict == edge.to_dict()
        types = {a["attribute_type_id"] for a in edge_dict.get("attributes", [])}
        assert "biolink:knowledge_level" not in types
        assert "biolink:agent_type" not in types


class TestPruneSupportGraphWalk:
    def test_prune_follows_support_graph_edges(self):
        kg = KnowledgeGraph(
            nodes={
                "n0": _node("biolink:Gene"),
                "n1": _node("biolink:Gene"),
                "n2": _node("biolink:Gene"),
            },
            edges={
                "e0": _edge(
                    "n0",
                    "n1",
                    attributes=[
                        Attribute(
                            attribute_type_id="biolink:support_graphs", value=["aux0"]
                        )
                    ],
                ),
                "e1": _edge("n1", "n2"),  # reachable only via aux0's support graph
                "e_orphan": _edge("n2", "n0"),  # unused
            },
        )
        result = Result(
            node_bindings={"qn0": [NodeBinding(id="n0", attributes=[])]},
            analyses=[
                Analysis(
                    resource_id="infores:x",
                    edge_bindings={"qe0": [EdgeBinding(id="e0", attributes=[])]},
                )
            ],
        )
        aux = {"aux0": AuxiliaryGraph(edges=["e1"], attributes=[])}
        kg_dict = kg.to_dict()
        kg.prune(aux, [result])
        KnowledgeGraphDictUtil.prune(
            kg_dict, {k: v.to_dict() for k, v in aux.items()}, [result.to_dict()]
        )
        assert kg_dict == kg.to_dict()
        assert set(kg_dict["edges"]) == {"e0", "e1"}  # e_orphan pruned
