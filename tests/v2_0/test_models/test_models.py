from typing import Any

from pydantic import ValidationError

from translator_tom import (
    Attribute,
    Biolink,
    Message,
    QEdge,
    QNode,
    QueryGraph,
    Response,
    Result,
    SetInterpretationEnum,
)


def test_qnode_null_properties():
    """Check that we can parse a QNode with None property values"""
    QNode.from_dict(
        {
            "ids": None,
            "categories": None,
        }
    )


def test_qedge_null_properties():
    """Check that we can parse a QEdge with None property values"""
    QEdge.from_dict(
        {
            "subject": "n0",
            "object": "n1",
            "predicates": None,
        }
    )


EXAMPLE_MESSAGE: dict[str, Any] = {
    "query_graph": {
        "nodes": {
            "n1": {"categories": ["biolink:ChemicalSubstance"]},
            "n2": {"categories": ["biolink:Disease"]},
        },
        "edges": {
            "n1n2": {
                "subject": "n1",
                "object": "n2",
                "predicates": ["biolink:related_to"],
            }
        },
    },
    "knowledge_graph": {
        "nodes": {
            "CHEBI:6801": {"categories": ["biolink:NamedThing"], "attributes": []},
            "MONDO:5148": {"categories": ["biolink:NamedThing"], "attributes": []},
            "CHEBI:6802": {"categories": ["biolink:NamedThing"], "attributes": []},
        },
        "edges": {
            "CHEBI:6801-biolink:treats-MONDO:5148": {
                "subject": "CHEBI:6801",
                "object": "MONDO:5148",
                "predicate": "biolink:treats",
                "knowledge_level": "knowledge_assertion",
                "agent_type": "manual_agent",
                "sources": [
                    {
                        "resource_id": "kp0",
                        "resource_role": "primary_knowledge_source",
                    }
                ],
                "attributes": [
                    {
                        "attribute_type_id": "biolink:attribute",
                        "value": {"sources": ["a", "b", "c"]},
                        "attributes": [
                            {
                                "attribute_type_id": "biolink:attribute",
                                "value": {"sources": ["a", "b", "c"]},
                                "attributes": [
                                    {
                                        "attribute_type_id": "biolink:attribute",
                                        "value": {"sources": ["a", "b", "c"]},
                                        "attributes": [
                                            {
                                                "attribute_type_id": "biolink:attribute",
                                                "value": {"sources": ["a", "b", "c"]},
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                ],
            },
            "CHEBI:6802-biolink:treats-MONDO:5148": {
                "subject": "CHEBI:6802",
                "object": "MONDO:5148",
                "predicate": "biolink:treats",
                "knowledge_level": "knowledge_assertion",
                "agent_type": "manual_agent",
                "sources": [
                    {
                        "resource_id": "kp0",
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
                "n1": {"ids": ["CHEBI:6801"]},
                "n2": {"ids": ["MONDO:5148"]},
            },
            "analyses": [
                {
                    "resource_id": "ara0",
                    "edge_bindings": {
                        "n1n2": {"ids": ["CHEBI:6801-biolink:treats-MONDO:5148"]}
                    },
                    "attributes": [],
                },
                {
                    "resource_id": "ara0",
                    "edge_bindings": {
                        "n1n2": {"ids": ["CHEBI:6802-biolink:treats-MONDO:5148"]}
                    },
                    "attributes": [],
                },
                {
                    "resource_id": "ara1",
                    "edge_bindings": {
                        "n1n2": {"ids": ["CHEBI:6801-biolink:treats-MONDO:5148"]}
                    },
                    "attributes": [],
                },
            ],
        }
    ],
    "auxiliary_graphs": {
        "a1": {"edges": ["CHEBI:6801-biolink:treats-MONDO:5148"]}
    },
}

EXAMPLE_MESSAGE_MULT: dict[str, Any] = {
    "query_graph": {
        "nodes": {
            "n0": {"categories": ["biolink:ChemicalSubstance"]},
            "n1": {"categories": ["biolink:Gene"]},
            "n2": {"categories": ["biolink:Disease"]},
        },
        "edges": {
            "n0n1": {
                "subject": "n0",
                "object": "n1",
                "predicates": ["biolink:related_to"],
            },
            "n1n2": {
                "subject": "n1",
                "object": "n2",
                "predicates": ["biolink:related_to"],
            },
        },
    },
    "knowledge_graph": {
        "nodes": {
            "CHEBI:6801": {"categories": ["biolink:NamedThing"], "attributes": []},
            "MONDO:5148": {"categories": ["biolink:NamedThing"], "attributes": []},
            "CHEBI:6802": {"categories": ["biolink:NamedThing"], "attributes": []},
            "CHEBI:6803": {"categories": ["biolink:NamedThing"], "attributes": []},
        },
        "edges": {
            "CHEBI:6801-biolink:related_to-MONDO:5148": {
                "subject": "CHEBI:6801",
                "object": "MONDO:5148",
                "predicate": "biolink:related_to",
                "knowledge_level": "knowledge_assertion",
                "agent_type": "manual_agent",
                "sources": [
                    {
                        "resource_id": "kp0",
                        "resource_role": "primary_knowledge_source",
                    }
                ],
                "attributes": [],
            },
            "CHEBI:6802-biolink:related_t0-MONDO:5148": {
                "subject": "CHEBI:6802",
                "object": "MONDO:5148",
                "predicate": "biolink:related_to",
                "knowledge_level": "knowledge_assertion",
                "agent_type": "manual_agent",
                "sources": [
                    {
                        "resource_id": "kp0",
                        "resource_role": "primary_knowledge_source",
                    }
                ],
                "attributes": [],
            },
            "CHEBI:6803-biolink:related_to-MONDO:5148": {
                "subject": "CHEBI:6803",
                "object": "MONDO:5148",
                "predicate": "biolink:related_to",
                "knowledge_level": "knowledge_assertion",
                "agent_type": "manual_agent",
                "sources": [
                    {
                        "resource_id": "kp0",
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
                "n0": {"ids": ["CHEBI:6803"]},
                "n1": {"ids": ["CHEBI:6801", "CHEBI:6802"]},
                "n2": {"ids": ["MONDO:5148"]},
            },
            "analyses": [
                {
                    "resource_id": "ara0",
                    "edge_bindings": {
                        "n1n2": {"ids": ["CHEBI:6801-biolink:treats-MONDO:5148"]}
                    },
                },
                {
                    "resource_id": "ara0",
                    "edge_bindings": {
                        "n1n2": {"ids": ["CHEBI:6802-biolink:treats-MONDO:5148"]}
                    },
                },
                {
                    "resource_id": "ara1",
                    "edge_bindings": {
                        "n1n2": {"ids": ["CHEBI:6801-biolink:treats-MONDO:5148"]}
                    },
                },
                {
                    "resource_id": "ara0",
                    "edge_bindings": {
                        "n0n1": {"ids": ["CHEBI:6803-biolink:treats-MONDO:5148"]}
                    },
                },
            ],
        }
    ],
    "auxiliary_graphs": {"a1": {"edges": ["CHEBI:6801-biolink:treats-MONDO:5148"]}},
}

PATHFINDER_MESSAGE: dict[str, Any] = {
    "query_graph": {
        "nodes": {
            "n0": {"ids": ["MONDO:0005011"]},
            "n1": {"ids": ["MONDO:0005180"]},
        },
        "paths": {
            "p0": {
                "subject": "n0",
                "object": "n1",
                "constraints": [
                    {"required_intermediate_categories": ["biolink:Gene"]}
                ],
            }
        },
    },
    "knowledge_graph": {
        "nodes": {
            "MONDO:0005011": {"categories": ["biolink:Disease"], "attributes": []},
            "MONDO:0005180": {"categories": ["biolink:Disease"], "attributes": []},
            "NCBIGene:120892": {"categories": ["biolink:Gene"], "attributes": []},
        },
        "edges": {
            "e0": {
                "subject": "MONDO:0005011",
                "object": "NCBIGene:120892",
                "predicate": "biolink:condition_associated_with_gene",
                "knowledge_level": "knowledge_assertion",
                "agent_type": "manual_agent",
                "sources": [
                    {
                        "resource_id": "kp0",
                        "resource_role": "primary_knowledge_source",
                    }
                ],
                "attributes": [
                    {
                        "attribute_type_id": "biolink:attribute",
                        "value": {"sources": ["a", "b", "c"]},
                        "attributes": [],
                    }
                ],
            },
            "e1": {
                "subject": "NCBIGene:120892",
                "object": "MONDO:0005180",
                "predicate": "biolink:biomarker_for",
                "knowledge_level": "knowledge_assertion",
                "agent_type": "manual_agent",
                "sources": [
                    {
                        "resource_id": "kp0",
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
                "n1": {"ids": ["MONDO:0005011"]},
                "n2": {"ids": ["MONDO:0005180"]},
            },
            "analyses": [
                {
                    "resource_id": "ara0",
                    "path_bindings": {"p0": {"ids": ["a0"]}},
                }
            ],
        }
    ],
    "auxiliary_graphs": {"a0": {"edges": ["e0", "e1"]}},
}

INVALID_PATHFINDER_QUERY: dict[str, Any] = {
    "query_graph": {
        "nodes": {
            "n0": {"ids": ["MONDO:0005011"]},
            "n1": {"ids": ["MONDO:0005180"]},
        },
        "paths": {
            "p0": {
                "subject": "n0",
                "object": "n1",
                "constraints": [{"required_intermediate_categories": []}],
            }
        },
    }
}


def test_message_hashable():
    """Check that we can hash a message"""

    m = Message.from_dict(EXAMPLE_MESSAGE)
    h = hash(m)
    assert h

    m2 = Message.from_dict(EXAMPLE_MESSAGE)
    h2 = hash(m2)

    assert h == h2


def test_message_jsonify():
    """Check that we can jsonify a message"""

    m = Message.from_dict(EXAMPLE_MESSAGE)
    m_json = m.to_json()
    m2 = Message.from_json(m_json)

    assert m == m2


def test_message_dictify():
    """Check that we can dictify a message"""

    m = Message.from_dict(EXAMPLE_MESSAGE)
    m_dict = m.to_dict()
    m2 = Message.from_dict(m_dict)

    assert m == m2

    assert type(next(iter(m_dict["results"]))) is dict


def test_hash_property_update():
    """Check that we can update the property of an object and the hash changes"""

    # Test on a QNode
    qnode = QNode.from_dict({"categories": ["biolink:ChemicalSubstance"]})

    h = hash(qnode)

    qnode.set_interpretation = SetInterpretationEnum.ALL.value

    assert hash(qnode) != h


def test_hash_list_update():
    """Check that we can update a list property on an object and the hash changes"""

    # Test on a QNode
    qnode = QNode.from_dict({"categories": ["biolink:ChemicalSubstance"]})
    h = hash(qnode)

    assert qnode.categories
    qnode.categories.append("biolink:Disease")
    assert hash(qnode) != h


def test_hash_dict_update():
    """Check that we can update a dict property on an object and the hash changes"""

    # Test on a QueryGraph
    kg = QueryGraph.from_dict(EXAMPLE_MESSAGE["query_graph"])
    h = hash(kg)

    kg.nodes["n0"] = kg.nodes["n1"]

    assert hash(kg) != h


def test_hash_deeply_nested_update():
    """
    Check that we can update a deeply nested object and the hash change is propogated
    """

    m = Message.from_dict(EXAMPLE_MESSAGE)
    h = hash(m)

    assert m.query_graph
    assert m.query_graph.nodes["n1"].categories
    m.query_graph.nodes["n1"].categories.append(Biolink("Gene"))

    assert hash(m) != h


def test_hash_attribute_values():
    """
    Check that we can hash a dictionary valued attribute
    """

    a = Attribute.from_dict(
        {
            "attribute_type_id": "biolink:knowledge_source",
            "value": {"sources": ["a", "b", "c"]},
        }
    )
    assert hash(a)


def test_merge_analyses():
    """
    Test that combine analyses function combines analyses
    """
    result = Result.from_dict(EXAMPLE_MESSAGE_MULT["results"][0])
    result.merge_analyses_by_resource_id()
    r = result.to_dict()
    assert len(r["analyses"]) == 2
    for analysis in r["analyses"]:
        if analysis["resource_id"] == "ara0":
            # A single EdgeBinding per QEdge; merged ids are unioned.
            assert len(analysis["edge_bindings"]["n1n2"]["ids"]) == 2
            assert len(analysis["edge_bindings"]["n0n1"]["ids"]) == 1


def test_response():
    """
    Test that response object is parsed properly
    """

    response = Response.from_dict({"message": EXAMPLE_MESSAGE})
    assert isinstance(response, Response)


def test_pathfinder_message():
    """
    Test that pathfinder messages can be parsed.
    """

    message = Message.from_dict(PATHFINDER_MESSAGE)

    assert isinstance(message, Message)


def test_invalid_pathfinder_query():
    """ "
    Test that pathfinder message with empty intermediate categories errors.
    """

    try:
        _ = Message.from_dict(INVALID_PATHFINDER_QUERY)
    except Exception as e:
        assert isinstance(e, ValidationError)
