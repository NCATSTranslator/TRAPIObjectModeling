from __future__ import annotations

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from trapi_object_modeling.qedge import QEdge
from trapi_object_modeling.qnode import QNode
from trapi_object_modeling.qpath import QPath
from trapi_object_modeling.shared import QEdgeID, QNodeID, QPathID


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
class BaseQueryGraph:
    """A graph representing a biomedical question.

    It serves as a template for
    each result (answer), where each bound knowledge graph node/edge is
    expected to obey the constraints of the associated query graph element.
    """

    nodes: dict[QNodeID, QNode]
    """The node specifications.

    The keys of this map are unique node
    identifiers and the corresponding values include the constraints
    on bound nodes.
    """


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
class QueryGraph(BaseQueryGraph):
    """A non-Pathfinder query SHOULD have edges following the QEdge schema and SHOULD NOT have paths."""

    edges: dict[QEdgeID, QEdge]
    """The edge specifications.

    The keys of this map are unique edge
    identifiers and the corresponding values include the constraints
    on bound edges, in addition to specifying the subject and object QNodes.
    """


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
class PathfinderQueryGraph(BaseQueryGraph):
    """A Pathfinder query SHOULD have paths following the QPath schema and SHOULD NOT have edges."""

    paths: dict[QPathID, QPath]
    """The QueryGraph path specification, used only for pathfinder type queries.

    The keys of this map are unique path identifiers and the
    corresponding values include the constraints on bound paths, in
    addition to specifying the subject, object, and intermediate QNodes.
    """
