from __future__ import annotations

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from trapi_object_modeling.meta_edge import MetaEdge
from trapi_object_modeling.meta_node import MetaNode
from trapi_object_modeling.shared import BiolinkEntity


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
class MetaKnowledgeGraph:
    """Knowledge-map representation of this TRAPI web service.

    The meta knowledge graph is composed of the union of most specific categories
    and predicates for each node and edge.
    """

    nodes: dict[BiolinkEntity, MetaNode]
    """Collection of the most specific node categories provided by this TRAPI web service, indexed by Biolink class CURIEs.

    A node category is only exposed here if there is
    node for which that is the most specific category available.
    """

    edges: list[MetaEdge]
    """List of the most specific edges/predicates provided by this TRAPI web service.

    A predicate is only exposed here if there is an edge
    for which the predicate is the most specific available.
    """
