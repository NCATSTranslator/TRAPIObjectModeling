from __future__ import annotations

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from trapi_object_modeling.models.auxiliary_graph import AuxiliaryGraphsDict
from trapi_object_modeling.models.knowledge_graph import KnowledgeGraph
from trapi_object_modeling.models.query_graph import PathfinderQueryGraph, QueryGraph
from trapi_object_modeling.models.result import Result
from trapi_object_modeling.utils.object_base import TOMBaseObject


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class Message(TOMBaseObject):
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

    auxiliary_graphs: AuxiliaryGraphsDict | None = None
    """Dictionary of AuxiliaryGraph instances that are used by Knowledge Graph Edges and Result Analyses.

    These are referenced elsewhere by the dictionary key.
    """

    @property
    def results_list(self) -> list[Result]:
        """Get the results as a guaranteed list, even if they are represented as None."""
        return self.results if self.results is not None else []

    @property
    def auxiliary_graphs_dict(self) -> AuxiliaryGraphsDict:
        """Get the auxiliary_graphs as a guaranteed dict, even if they are represented as None."""
        return self.auxiliary_graphs if self.auxiliary_graphs is not None else {}

    def normalize(self) -> None:
        """Normalize the knowledge_graph and update the results and auxiliary_graphs accordingly."""
        if self.knowledge_graph is None:
            return

        mapping = self.knowledge_graph.normalize()

        for auxg in self.auxiliary_graphs_dict.values():
            auxg.normalize(mapping)

        for result in self.results_list:
            result.normalize(mapping)

    def prune_kg(self) -> None:
        """Prune the knowledge_graph."""
        if self.knowledge_graph is None:
            return
        self.knowledge_graph.prune(self.auxiliary_graphs_dict, self.results_list)
