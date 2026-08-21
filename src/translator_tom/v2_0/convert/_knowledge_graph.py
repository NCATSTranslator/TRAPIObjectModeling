"""Transforms for KnowledgeGraph and Edge."""

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
    register,
)
from translator_tom.v2_0.models.knowledge_graph import Edge, KnowledgeGraph


@register(V16Edge, Edge)
def _upgrade_edge(data: dict[str, Any], **_: Any) -> dict[str, Any]:
    """Lift knowledge_level/agent_type out of `attributes` into top-level fields.

    Missing KL/AT defaults to biolink `not_provided`; the two lifted attribute
    entries are removed from the remaining attributes.
    """
    data = dict(data)  # copy: transforms reassign keys, never mutate the caller's dict

    knowledge_level = DEFAULT_KNOWLEDGE_LEVEL
    agent_type = DEFAULT_AGENT_TYPE
    remaining: list[dict[str, Any]] = []
    # raw 1.6 dicts may carry a null `attributes` or null values; treat null as absent
    for attribute in data.get("attributes") or []:
        type_id = attribute.get("attribute_type_id")
        if type_id == KNOWLEDGE_LEVEL_ATTRIBUTE_ID:
            knowledge_level = attribute.get("value") or knowledge_level
        elif type_id == AGENT_TYPE_ATTRIBUTE_ID:
            agent_type = attribute.get("value") or agent_type
        else:
            remaining.append(attribute)

    data["knowledge_level"] = knowledge_level
    data["agent_type"] = agent_type
    if remaining:
        data["attributes"] = remaining
    else:
        data.pop("attributes", None)

    return data


@register(V16KnowledgeGraph, KnowledgeGraph)
def _upgrade_knowledge_graph(data: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Convert each Edge (KL/AT lift); nodes pass through (cleaned by the outer prune)."""
    data = dict(data)

    edges = data.get("edges")
    if edges:
        data["edges"] = {
            edge_id: _upgrade_edge(edge, **kwargs) for edge_id, edge in edges.items()
        }
    else:
        data.pop("edges", None)

    return data
