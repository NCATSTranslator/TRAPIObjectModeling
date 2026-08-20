"""Converters for KnowledgeGraph and Edge."""

from __future__ import annotations

from typing import Any

from translator_tom.v1_6.models.knowledge_graph import Edge as V16Edge
from translator_tom.v1_6.models.knowledge_graph import (
    KnowledgeGraph as V16KnowledgeGraph,
)
from translator_tom.v2_0.convert._util import (
    AGENT_TYPE_ATTRIBUTE_ID,
    DEFAULT_AGENT_TYPE,
    DEFAULT_KNOWLEDGE_LEVEL,
    KNOWLEDGE_LEVEL_ATTRIBUTE_ID,
    _build,
    up_version,
)
from translator_tom.v2_0.models.knowledge_graph import Edge, KnowledgeGraph


@up_version.register(V16Edge)
def _convert_edge(obj: V16Edge, **_: Any) -> Edge:
    """Lift knowledge_level/agent_type out of `attributes` into top-level fields.

    Missing KL/AT defaults to biolink `not_provided`; the two lifted attribute
    entries are removed from the remaining attributes.
    """
    data = obj.to_dict()

    knowledge_level = DEFAULT_KNOWLEDGE_LEVEL
    agent_type = DEFAULT_AGENT_TYPE
    remaining: list[dict[str, Any]] = []
    for attribute in data.get("attributes", []):
        type_id = attribute.get("attribute_type_id")
        if type_id == KNOWLEDGE_LEVEL_ATTRIBUTE_ID:
            knowledge_level = attribute.get("value", knowledge_level)
        elif type_id == AGENT_TYPE_ATTRIBUTE_ID:
            agent_type = attribute.get("value", agent_type)
        else:
            remaining.append(attribute)

    data["knowledge_level"] = knowledge_level
    data["agent_type"] = agent_type
    if remaining:
        data["attributes"] = remaining
    else:
        data.pop("attributes", None)

    return _build(Edge, data)


@up_version.register(V16KnowledgeGraph)
def _convert_knowledge_graph(obj: V16KnowledgeGraph, **kwargs: Any) -> KnowledgeGraph:
    """Convert each Edge (KL/AT lift); nodes pass through unchanged."""
    data = obj.to_dict()

    if obj.edges:
        data["edges"] = {
            edge_id: up_version(edge, **kwargs).to_dict()
            for edge_id, edge in obj.edges.items()
        }
    else:
        data.pop("edges", None)

    return _build(KnowledgeGraph, data)
