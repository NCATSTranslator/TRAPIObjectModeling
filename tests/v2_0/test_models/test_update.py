from typing import Any

from translator_tom import (
    Analysis,
    Attribute,
    Edge,
    Message,
    Result,
    RetrievalSource,
)

# Some sample attributes
ATTRIBUTE_A = Attribute.from_dict(
    {
        "attribute_type_id": "biolink:knowledge_source",
        "value": "https://automat.renci.org/",
        "attributes": [
            {"attribute_type_id": "biolink:publication", "value": "pubmed_central"},
            {"attribute_type_id": "biolink:has_p-value_evidence", "value": 0.04},
        ],
    }
)

ATTRIBUTE_B = Attribute.from_dict(
    {
        "attribute_type_id": "biolink:publication",
        "value": "pubmed_central",
        "attributes": [
            {"attribute_type_id": "biolink:has_original_source", "value": True},
        ],
    }
)


def _kedge(subject: str, object_: str, resource_id: str) -> dict[str, Any]:
    """A minimal 2.0 KG edge (KL/AT are required top-level fields)."""
    return {
        "subject": subject,
        "object": object_,
        "predicate": "biolink:ameliorates",
        "knowledge_level": "knowledge_assertion",
        "agent_type": "manual_agent",
        "sources": [
            {"resource_id": resource_id, "resource_role": "primary_knowledge_source"}
        ],
        "attributes": [],
    }


def test_result_merging():
    """Test that duplicate results and analyses are merged correctly"""

    message: dict[str, Any] = {
        "knowledge_graph": {
            "nodes": {},
            "edges": {
                "ke0": _kedge("kn0", "kn1", "kp0"),
                "ke1": _kedge("kn0", "kn1", "kp1"),
            },
        },
        "results": [
            {
                "node_bindings": {"n0": {"ids": ["kn0"]}},
                "analyses": [
                    {
                        "resource_id": "ara0",
                        "edge_bindings": {"e0": {"ids": ["ke0"]}},
                        "attributes": [],
                    }
                ],
            },
            {
                "node_bindings": {"n0": {"ids": ["kn0"]}},
                "analyses": [
                    {
                        "resource_id": "ara0",
                        "edge_bindings": {"e0": {"ids": ["ke0"]}},
                        "attributes": [],
                    },
                    {
                        "resource_id": "ara1",
                        "edge_bindings": {"e0": {"ids": ["ke0"]}},
                        "attributes": [],
                    },
                ],
            },
        ],
    }

    m = Message.from_dict(message)
    assert m.results is not None
    Result.merge_results(m.results)
    assert len(m.results) == 1
    analyses = next(iter(m.results)).analyses
    assert analyses is not None
    assert len(analyses) == 2


def test_different_result_merging():
    """Test that different results are not merged"""

    message: dict[str, Any] = {
        "knowledge_graph": {
            "nodes": {},
            "edges": {
                "ke0": _kedge("kn0", "kn1", "kp0"),
                "ke1": _kedge("kn0", "kn1", "kp1"),
            },
        },
        "results": [
            {
                "node_bindings": {"n0": {"ids": ["kn0"]}},
                "analyses": [
                    {
                        "resource_id": "ara0",
                        "edge_bindings": {"e0": {"ids": ["ke0"]}},
                        "attributes": [],
                    }
                ],
            },
            {
                "node_bindings": {"n0": {"ids": ["kn1"]}},
                "analyses": [
                    {
                        "resource_id": "ara0",
                        "edge_bindings": {"e0": {"ids": ["ke0"]}},
                        "attributes": [],
                    },
                    {
                        "resource_id": "ara1",
                        "edge_bindings": {"e0": {"ids": ["ke0"]}},
                        "attributes": [],
                    },
                ],
            },
        ],
    }
    m = Message.from_dict(message)
    assert m.results
    assert len(m.results) == 2


def test_deduplicate_results_out_of_order():
    """
    Test that we successfully deduplicate results when given
    the same results but in a different order
    """

    message: dict[str, Any] = {
        "knowledge_graph": {
            "nodes": {},
            "edges": {
                "ke0": _kedge("kn0", "kn1", "kp0"),
                "ke1": _kedge("kn0", "kn1", "kp1"),
            },
        },
        "results": [
            {
                "node_bindings": {"a": {"ids": ["MONDO:0011122", "CHEBI:88916"]}},
                "analyses": [
                    {
                        "resource_id": "ara0",
                        "edge_bindings": {"e0": {"ids": ["ke0"]}},
                        "attributes": [],
                    }
                ],
            },
            {
                "node_bindings": {"a": {"ids": ["CHEBI:88916", "MONDO:0011122"]}},
                "analyses": [
                    {
                        "resource_id": "ara0",
                        "edge_bindings": {"e0": {"ids": ["ke0"]}},
                        "attributes": [],
                    },
                    {
                        "resource_id": "ara1",
                        "edge_bindings": {"e0": {"ids": ["ke0"]}},
                        "attributes": [],
                    },
                ],
            },
        ],
    }

    m = Message.from_dict(message)
    assert m.results is not None
    Result.merge_results(m.results)
    assert len(m.results) == 1


def test_deduplicate_results_different():
    """
    Test that we don't deduplicate results when given
    different binding information
    """

    message: dict[str, Any] = {
        "knowledge_graph": {"nodes": {}, "edges": {}},
        "results": [
            {
                "node_bindings": {"b": {"ids": ["CHEBI:88916", "MONDO:0011122"]}},
            },
            {
                "node_bindings": {"a": {"ids": ["MONDO:0011122", "CHEBI:88916"]}},
            },
        ],
    }

    m = Message.from_dict(message)
    assert m.results is not None
    assert len(m.results) == 2


def test_merge_knowledge_graph_nodes():
    """
    Test that we do a smart merge when given knowledge
    graph nodes with the same keys
    """

    message_a: dict[str, Any] = {
        "knowledge_graph": {
            "nodes": {
                "MONDO:1": {
                    "name": "Ebola",
                    "categories": ["biolink:Disease"],
                    "attributes": [ATTRIBUTE_A],
                }
            },
            "edges": {},
        },
        "results": [],
    }

    message_b: dict[str, Any] = {
        "knowledge_graph": {
            "nodes": {
                "MONDO:1": {
                    "name": "Ebola Hemorrhagic Fever",
                    "categories": ["biolink:DiseaseOrPhenotypicFeature"],
                    "attributes": [ATTRIBUTE_B],
                }
            },
            "edges": {},
        },
        "results": [],
    }

    m = Message()

    m.update(Message.from_dict(message_a))
    m.update(Message.from_dict(message_b))

    # Validate output
    assert m.knowledge_graph is not None
    nodes = m.knowledge_graph.nodes
    assert len(nodes) == 1
    node = next(iter(nodes.values()))

    assert node.attributes is not None
    assert ATTRIBUTE_A in node.attributes
    assert ATTRIBUTE_B in node.attributes


def test_normalize_knowledge_graph_edges():
    """
    Test that KG edge IDs are normalized, so even if we pass
    in edges with the same name they are not merged by default
    """

    message_a: dict[str, Any] = {
        "knowledge_graph": {
            "nodes": {
                "MONDO:1": {"categories": ["biolink:NamedThing"], "attributes": []},
                "CHEBI:1": {"categories": ["biolink:NamedThing"], "attributes": []},
            },
            "edges": {
                "n0n1": {
                    "subject": "MONDO:1",
                    "object": "CHEBI:1",
                    "predicate": "biolink:treated_by",
                    "knowledge_level": "knowledge_assertion",
                    "agent_type": "manual_agent",
                    "attributes": [ATTRIBUTE_A],
                    "sources": [
                        {
                            "resource_id": "kp0",
                            "resource_role": "primary_knowledge_source",
                        }
                    ],
                }
            },
        },
        "results": [
            {
                "node_bindings": {
                    "a": {"ids": ["MONDO:1"]},
                    "b": {"ids": ["CHEBI:1"]},
                },
                "analyses": [
                    {
                        "resource_id": "ara0",
                        "edge_bindings": {"qe0": {"ids": ["n0n1"]}},
                    }
                ],
            }
        ],
    }

    message_b: dict[str, Any] = {
        "knowledge_graph": {
            "nodes": {
                "MONDO:1": {"categories": ["biolink:NamedThing"], "attributes": []},
                "CHEBI:1": {"categories": ["biolink:NamedThing"], "attributes": []},
            },
            "edges": {
                "n0n1": {
                    "subject": "MONDO:1",
                    "object": "CHEBI:1",
                    "predicate": "biolink:treated_by",
                    "knowledge_level": "knowledge_assertion",
                    "agent_type": "manual_agent",
                    "attributes": [ATTRIBUTE_B],
                    "sources": [
                        {
                            "resource_id": "kp1",
                            "resource_role": "primary_knowledge_source",
                        }
                    ],
                }
            },
        },
        "results": [],
    }

    m = Message()

    m_a = Message.from_dict(message_a)
    m_b = Message.from_dict(message_b)

    m.update(m_a)
    m.update(m_b)

    # Check that we didn't combine edges
    assert m.knowledge_graph is not None
    edges = m.knowledge_graph.edges
    assert edges is not None
    assert len(edges) == 2

    # Check that the result was updated to point to the correct edge
    edge_id, _ = next(iter(edges.items()))
    assert m.results is not None
    result = next(iter(m.results))
    assert result.analyses is not None
    analysis = next(iter(result.analyses))
    assert isinstance(analysis, Analysis)
    assert analysis.edge_bindings is not None
    assert analysis.edge_bindings["qe0"].ids == [edge_id]


def test_merge_identical_attributes():
    """
    Tests that identical attributes are merged
    """

    message_a: dict[str, Any] = {
        "knowledge_graph": {
            "nodes": {
                "MONDO:1": {
                    "name": "Ebola",
                    "categories": ["biolink:Disease"],
                    "attributes": [ATTRIBUTE_A],
                }
            },
            "edges": {},
        },
        "results": [],
    }

    message_b: dict[str, Any] = {
        "knowledge_graph": {
            "nodes": {
                "MONDO:1": {
                    "name": "Ebola Hemorrhagic Fever",
                    "categories": ["biolink:DiseaseOrPhenotypicFeature"],
                    "attributes": [ATTRIBUTE_A],
                }
            },
            "edges": {},
        },
        "results": [],
    }

    m = Message()

    m.update(Message.from_dict(message_a))
    m.update(Message.from_dict(message_b))

    # Validate output
    assert m.knowledge_graph is not None
    nodes = m.knowledge_graph.nodes
    assert len(nodes) == 1
    node = next(iter(nodes.values()))

    assert node.attributes is not None
    assert ATTRIBUTE_A in node.attributes
    assert len(node.attributes) == 1


def test_merge_knowledge_graph_edges():
    """
    Test that knowledge graph edges are merged properly
    """

    def _agg_edge(kp: str) -> dict[str, Any]:
        return {
            "subject": "kn0",
            "object": "kn1",
            "predicate": "biolink:ameliorates",
            "knowledge_level": "knowledge_assertion",
            "agent_type": "automated_agent",
            "sources": [
                {"resource_id": "ks0", "resource_role": "primary_knowledge_source"},
                {
                    "resource_id": kp,
                    "resource_role": "aggregator_knowledge_source",
                    "upstream_resource_ids": ["ks0"],
                },
                {
                    "resource_id": "ara0",
                    "resource_role": "aggregator_knowledge_source",
                    "upstream_resource_ids": [kp],
                },
            ],
            "attributes": [],
        }

    message_a: dict[str, Any] = {
        "knowledge_graph": {"nodes": {}, "edges": {"ke0": _agg_edge("kp0")}},
        "results": [],
    }
    message_b: dict[str, Any] = {
        "knowledge_graph": {"nodes": {}, "edges": {"ke0": _agg_edge("kp1")}},
        "results": [],
    }

    m = Message()

    m.update(Message.from_dict(message_a))
    m.update(Message.from_dict(message_b))

    assert m.knowledge_graph is not None
    edges = m.knowledge_graph.edges
    assert edges is not None
    assert len(edges) == 1
    edge = next(iter(edges.values()))

    sources = edge.sources
    assert len(sources) == 4
    for source in sources:
        if source.resource_id == "ara0":
            assert source.upstream_resource_ids is not None
            assert len(source.upstream_resource_ids) == 2


def _isolation_message(tag: str, val: int) -> dict[str, Any]:
    """A message sharing an edge (``shared``) with every other tag, plus a tag-unique edge."""
    return {
        "knowledge_graph": {
            "nodes": {
                "n0": {
                    "name": tag,
                    "categories": ["biolink:NamedThing"],
                    "attributes": [{"attribute_type_id": "biolink:x", "value": val}],
                }
            },
            "edges": {
                "shared": {
                    "subject": "n0",
                    "object": "n0",
                    "predicate": "biolink:related_to",
                    "knowledge_level": "knowledge_assertion",
                    "agent_type": "manual_agent",
                    "sources": [
                        {
                            "resource_id": "ks",
                            "resource_role": "primary_knowledge_source",
                        }
                    ],
                    "attributes": [{"attribute_type_id": "biolink:y", "value": val}],
                },
                f"e{tag}": {
                    "subject": "n0",
                    "object": "n0",
                    "predicate": "biolink:related_to",
                    "knowledge_level": "knowledge_assertion",
                    "agent_type": "manual_agent",
                    "sources": [
                        {
                            "resource_id": f"ks{tag}",
                            "resource_role": "primary_knowledge_source",
                        }
                    ],
                    "attributes": [],
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
                        "attributes": [],
                    }
                ],
            }
        ],
        "auxiliary_graphs": {f"aux{tag}": {"edges": ["shared"]}},
    }


def test_message_update_does_not_mutate_or_alias_other():
    """Message.update must fully isolate `other`: never mutate it, never alias it into self."""
    a = Message.from_dict(_isolation_message("A", 1))
    b = Message.from_dict(_isolation_message("B", 2))

    b_before = b.to_json()
    a.update(b)
    # `other` is untouched by the update.
    assert b.to_json() == b_before

    # Mutating everything reachable in `a` must not leak into `b`.
    b_snapshot = b.to_json()
    assert a.knowledge_graph and a.results and a.auxiliary_graphs
    for edge in a.knowledge_graph.edges.values():
        edge.attributes = [Attribute(attribute_type_id="biolink:MUT", value=0)]
        edge.sources[0].resource_id = "MUT"
    for node in a.knowledge_graph.nodes.values():
        node.name = "MUT"
        node.attributes = []
    for result in a.results:
        result.analyses = []
    for graph in a.auxiliary_graphs.values():
        graph.edges = ["MUT"]
    assert b.to_json() == b_snapshot


def test_message_update_isolates_other_in_both_mode():
    """The pre_normalized fast paths must isolate `other` too (previously aliased)."""
    a = Message.from_dict(_isolation_message("A", 1))
    b = Message.from_dict(_isolation_message("B", 2))
    a.normalize()
    b.normalize()

    b_before = b.to_json()
    a.update(b, pre_normalized="both")
    assert b.to_json() == b_before

    b_snapshot = b.to_json()
    assert a.knowledge_graph and a.results and a.auxiliary_graphs
    for result in a.results:
        result.analyses = []
    for graph in a.auxiliary_graphs.values():
        graph.edges = ["MUT"]
    for edge in a.knowledge_graph.edges.values():
        edge.attributes = [Attribute(attribute_type_id="biolink:MUT", value=0)]
    assert b.to_json() == b_snapshot


def test_message_update_isolates_denormalized_other():
    """A denormalized `other` (edges colliding on hash) is not mutated by the merge.

    normalize merges the colliding edges; because update feeds it a shallow copy of
    `other`, that merge must not touch the caller's edge objects.
    """
    dup: dict[str, Any] = {
        "knowledge_graph": {
            "nodes": {},
            "edges": {
                # Same subject/object/predicate/primary-source -> identical hash.
                "k1": {
                    "subject": "n0",
                    "object": "n1",
                    "predicate": "biolink:related_to",
                    "knowledge_level": "knowledge_assertion",
                    "agent_type": "manual_agent",
                    "sources": [
                        {
                            "resource_id": "ks",
                            "resource_role": "primary_knowledge_source",
                        }
                    ],
                    "attributes": [{"attribute_type_id": "biolink:a", "value": 1}],
                },
                "k2": {
                    "subject": "n0",
                    "object": "n1",
                    "predicate": "biolink:related_to",
                    "knowledge_level": "knowledge_assertion",
                    "agent_type": "manual_agent",
                    "sources": [
                        {
                            "resource_id": "ks",
                            "resource_role": "primary_knowledge_source",
                        }
                    ],
                    "attributes": [{"attribute_type_id": "biolink:b", "value": 2}],
                },
            },
        },
        "results": [],
    }
    b = Message.from_dict(dup)
    b_before = b.to_json()
    Message().update(b)
    assert b.to_json() == b_before


def test_knowledge_graph_update_copies_on_insert():
    """KnowledgeGraph.update must not mutate `other` or alias its node/edge objects."""
    a = Message.from_dict(_isolation_message("A", 1)).knowledge_graph
    b = Message.from_dict(_isolation_message("B", 2)).knowledge_graph
    assert a is not None and b is not None

    b_before = b.to_json()
    a.update(b)
    assert b.to_json() == b_before  # other unmutated

    b_snapshot = b.to_json()
    for edge in a.edges.values():
        edge.attributes = [Attribute(attribute_type_id="biolink:MUT", value=0)]
    for node in a.nodes.values():
        node.name = "MUT"
    assert b.to_json() == b_snapshot  # inserted objects were copied, not aliased


def test_edge_update_does_not_mutate_or_alias_other():
    """Edge.update must not mutate `other` or alias its attributes/sources into self."""

    def edge(attr_val: int) -> Edge:
        return Edge(
            subject="n0",
            object="n1",
            predicate="biolink:related_to",
            knowledge_level="knowledge_assertion",
            agent_type="manual_agent",
            attributes=[Attribute(attribute_type_id="biolink:y", value=attr_val)],
            sources=[
                RetrievalSource(
                    resource_id="ks", resource_role="primary_knowledge_source"
                )
            ],
        )

    a, b = edge(1), edge(2)
    b_before = b.to_json()
    a.update(b)
    assert b.to_json() == b_before  # other unmutated

    b_snapshot = b.to_json()
    for attr in a.attributes_list:
        attr.value = 999
    for source in a.sources:
        source.resource_id = "MUT"
    assert b.to_json() == b_snapshot  # merged attrs/sources were copied
