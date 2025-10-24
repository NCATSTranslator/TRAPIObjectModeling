from __future__ import annotations

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from trapi_object_modeling.edge import Edge
from trapi_object_modeling.node import Node
from trapi_object_modeling.shared import CURIE, EdgeID


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
class KnowledgeGraph:
    """The knowledge graph associated with a set of results.

    The instances of Node and Edge defining this graph represent instances of
    biolink:NamedThing (concept nodes) and biolink:Association
    (relationship edges) representing (Attribute) annotated knowledge
    returned from the knowledge sources and inference agents wrapped by
    the given TRAPI implementation.
    """

    nodes: dict[CURIE, Node]
    """Dictionary of Node instances used in the KnowledgeGraph, referenced elsewhere in the TRAPI output by the dictionary key."""

    edges: dict[EdgeID, Edge]
    """Dictionary of Edge instances used in the KnowledgeGraph, referenced elsewhere in the TRAPI output by the dictionary key."""
