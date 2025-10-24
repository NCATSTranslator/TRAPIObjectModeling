from __future__ import annotations

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from trapi_object_modeling.auxiliary_graph import AuxiliaryGraph
from trapi_object_modeling.knowledge_graph import KnowledgeGraph
from trapi_object_modeling.query_graph import PathfinderQueryGraph, QueryGraph
from trapi_object_modeling.result import Result
from trapi_object_modeling.shared import AuxGraphID


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class Message:
    """The message object holds the main content of a Query or a Response in three properties: query_graph, results, and knowledge_graph.

    The query_graph property contains the query configuration, the results
    property contains any answers that are returned by the service,
    and knowledge_graph property contains lists of edges and nodes in the
    thought graph corresponding to this message. The content of these
    properties is context-dependent to the encompassing object and
    the TRAPI operation requested.
    """

    results: list[Result] | None = None
    """List of all returned Result objects for the query posed.

    The list SHOULD NOT be assumed to be ordered. The 'score' property,
    if present, MAY be used to infer result rankings. If Results are
    not expected (such as for a query Message), this property SHOULD
    be null or absent. If Results are expected (such as for a response
    Message) and no Results are available, this property SHOULD be an
    array with 0 Results in it.
    """

    query_graph: QueryGraph | PathfinderQueryGraph | None = None
    """QueryGraph object that contains a serialization of a query in the form of a graph."""

    knowledge_graph: KnowledgeGraph | None = None
    """KnowledgeGraph object that contains lists of nodes and edges in the thought graph corresponding to the message."""

    auxiliary_graphs: dict[AuxGraphID, AuxiliaryGraph] | None = None
    """Dictionary of AuxiliaryGraph instances that are used by Knowledge Graph Edges and Result Analyses.

    These are referenced elsewhere by the dictionary key.
    """
