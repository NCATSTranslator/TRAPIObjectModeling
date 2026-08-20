from typing import Any

from translator_tom.v1_6 import (
    Analysis,
    Attribute,
    Edge,
    KnowledgeGraph,
    Message,
    RetrievalSource,
    Result,
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


def test_result_merging():
    """Test that duplicate results and analyses are merged correctly"""

    message: dict[str, Any] = {
        "knowledge_graph": {
            "nodes": {},
            "edges": {
                "ke0": {
                    "subject": "kn0",
                    "object": "kn1",
                    "predicate": "biolink:ameliorates",
                    "sources": [
                        {
                            "resource_id": "kp0",
                            "resource_role": "primary_knowledge_source",
                        }
                    ],
                    "attributes": [],
                },
                "ke1": {
                    "subject": "kn0",
                    "object": "kn1",
                    "predicate": "biolink:ameliorates",
                    "sources": [
                        {
                            "resource_id": "kp1",
                            "resource_role": "primary_knowledge_source",
                        }
                    ],
                    "attributes": [],
                },
            },
        },
        "results": [
            {
                "node_bindings": {"n0": [{"id": "kn0", "attributes": []}]},
                "analyses": [
                    {
                        "resource_id": "ara0",
                        "edge_bindings": {"e0": [{"id": "ke0", "attributes": []}]},
                        "attributes": [],
                    }
                ],
            },
            {
                "node_bindings": {"n0": [{"id": "kn0", "attributes": []}]},
                "analyses": [
                    {
                        "resource_id": "ara0",
                        "edge_bindings": {"e0": [{"id": "ke0", "attributes": []}]},
                        "attributes": [],
                    },
                    {
                        "resource_id": "ara1",
                        "edge_bindings": {"e0": [{"id": "ke0", "attributes": []}]},
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
    assert len(next(iter(m.results)).analyses) == 2


def test_different_result_merging():
    """Test that different results are not merged"""

    message: dict[str, Any] = {
        "knowledge_graph": {
            "nodes": {},
            "edges": {
                "ke0": {
                    "subject": "kn0",
                    "object": "kn1",
                    "predicate": "biolink:ameliorates",
                    "sources": [
                        {
                            "resource_id": "kp0",
                            "resource_role": "primary_knowledge_source",
                        }
                    ],
                    "attributes": [],
                },
                "ke1": {
                    "subject": "kn0",
                    "object": "kn1",
                    "predicate": "biolink:ameliorates",
                    "sources": [
                        {
                            "resource_id": "kp1",
                            "resource_role": "primary_knowledge_source",
                        }
                    ],
                    "attributes": [],
                },
            },
        },
        "results": [
            {
                "node_bindings": {"n0": [{"id": "kn0", "attributes": []}]},
                "analyses": [
                    {
                        "resource_id": "ara0",
                        "edge_bindings": {"e0": [{"id": "ke0", "attributes": []}]},
                        "attributes": [],
                    }
                ],
            },
            {
                "node_bindings": {"n0": [{"id": "kn1", "attributes": []}]},
                "analyses": [
                    {
                        "resource_id": "ara0",
                        "edge_bindings": {"e0": [{"id": "ke0", "attributes": []}]},
                        "attributes": [],
                    },
                    {
                        "resource_id": "ara1",
                        "edge_bindings": {"e0": [{"id": "ke0", "attributes": []}]},
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
                "ke0": {
                    "subject": "kn0",
                    "object": "kn1",
                    "predicate": "biolink:ameliorates",
                    "sources": [
                        {
                            "resource_id": "kp0",
                            "resource_role": "primary_knowledge_source",
                        }
                    ],
                    "attributes": [],
                },
                "ke1": {
                    "subject": "kn0",
                    "object": "kn1",
                    "predicate": "biolink:ameliorates",
                    "sources": [
                        {
                            "resource_id": "kp1",
                            "resource_role": "primary_knowledge_source",
                        }
                    ],
                    "attributes": [],
                },
            },
        },
        "results": [
            {
                "node_bindings": {
                    "a": [
                        {"id": "MONDO:0011122", "attributes": []},
                        {"id": "CHEBI:88916", "attributes": []},
                    ]
                },
                "analyses": [
                    {
                        "resource_id": "ara0",
                        "edge_bindings": {"e0": [{"id": "ke0", "attributes": []}]},
                        "attributes": [],
                    }
                ],
            },
            {
                "node_bindings": {
                    "a": [
                        {"id": "CHEBI:88916", "attributes": []},
                        {"id": "MONDO:0011122", "attributes": []},
                    ],
                },
                "analyses": [
                    {
                        "resource_id": "ara0",
                        "edge_bindings": {"e0": [{"id": "ke0", "attributes": []}]},
                        "attributes": [],
                    },
                    {
                        "resource_id": "ara1",
                        "edge_bindings": {"e0": [{"id": "ke0", "attributes": []}]},
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
                "node_bindings": {
                    "b": [
                        {"id": "CHEBI:88916", "attributes": []},
                        {"id": "MONDO:0011122", "attributes": []},
                    ],
                },
                "analyses": [],
            },
            {
                "node_bindings": {
                    "a": [
                        {"id": "MONDO:0011122", "attributes": []},
                        {"id": "CHEBI:88916", "attributes": []},
                    ],
                },
                "analyses": [],
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
                    "a": [{"id": "MONDO:1", "attributes": []}],
                    "b": [{"id": "CHEBI:1", "attributes": []}],
                },
                "analyses": [
                    {
                        "resource_id": "ara0",
                        "edge_bindings": {"qe0": [{"id": "n0n1", "attributes": []}]},
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
    assert len(edges) == 2

    # Check that the result was updated to point to the correct edge
    edge_id, _ = next(iter(edges.items()))
    assert m.results is not None
    result = next(iter(m.results))
    analysis = next(iter(result.analyses))
    assert isinstance(analysis, Analysis)
    assert next(iter(analysis.edge_bindings["qe0"])).id == edge_id


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

    print(m)
    print()

    m.update(Message.from_dict(message_b))

    print(m)
    # Validate output
    assert m.knowledge_graph is not None
    nodes = m.knowledge_graph.nodes
    assert len(nodes) == 1
    node = next(iter(nodes.values()))

    assert ATTRIBUTE_A in node.attributes
    assert len(node.attributes) == 1


def test_merge_knowledge_graph_edges():
    """
    Test that knowledge graph edges are merged properly
    """

    message_a: dict[str, Any] = {
        "knowledge_graph": {
            "nodes": {},
            "edges": {
                "ke0": {
                    "subject": "kn0",
                    "object": "kn1",
                    "predicate": "biolink:ameliorates",
                    "sources": [
                        {
                            "resource_id": "ks0",
                            "resource_role": "primary_knowledge_source",
                        },
                        {
                            "resource_id": "kp0",
                            "resource_role": "aggregator_knowledge_source",
                            "upstream_resource_ids": ["ks0"],
                        },
                        {
                            "resource_id": "ara0",
                            "resource_role": "aggregator_knowledge_source",
                            "upstream_resource_ids": ["kp0"],
                        },
                    ],
                    "attributes": [
                        {
                            "attribute_type_id": "biolink:agent_type",
                            "value": "automated_agent",
                        }
                    ],
                }
            },
        },
        "results": [],
    }

    message_b: dict[str, Any] = {
        "knowledge_graph": {
            "nodes": {},
            "edges": {
                "ke0": {
                    "subject": "kn0",
                    "object": "kn1",
                    "predicate": "biolink:ameliorates",
                    "sources": [
                        {
                            "resource_id": "ks0",
                            "resource_role": "primary_knowledge_source",
                        },
                        {
                            "resource_id": "kp1",
                            "resource_role": "aggregator_knowledge_source",
                            "upstream_resource_ids": ["ks0"],
                        },
                        {
                            "resource_id": "ara0",
                            "resource_role": "aggregator_knowledge_source",
                            "upstream_resource_ids": ["kp1"],
                        },
                    ],
                    "attributes": [
                        {
                            "attribute_type_id": "biolink:agent_type",
                            "value": "automated_agent",
                        }
                    ],
                }
            },
        },
        "results": [],
    }

    m = Message()

    m.update(Message.from_dict(message_a))
    m.update(Message.from_dict(message_b))

    assert m.knowledge_graph is not None
    edges = m.knowledge_graph.edges
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
                    "sources": [
                        {"resource_id": "ks", "resource_role": "primary_knowledge_source"}
                    ],
                    "attributes": [{"attribute_type_id": "biolink:y", "value": val}],
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
                    "attributes": [],
                },
            },
        },
        "results": [
            {
                "node_bindings": {"n0": [{"id": "n0", "attributes": []}]},
                "analyses": [
                    {
                        "resource_id": f"ara{tag}",
                        "edge_bindings": {"e0": [{"id": "shared", "attributes": []}]},
                        "attributes": [],
                    }
                ],
            }
        ],
        "auxiliary_graphs": {f"aux{tag}": {"edges": ["shared"], "attributes": []}},
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
                    "sources": [
                        {"resource_id": "ks", "resource_role": "primary_knowledge_source"}
                    ],
                    "attributes": [{"attribute_type_id": "biolink:a", "value": 1}],
                },
                "k2": {
                    "subject": "n0",
                    "object": "n1",
                    "predicate": "biolink:related_to",
                    "sources": [
                        {"resource_id": "ks", "resource_role": "primary_knowledge_source"}
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
