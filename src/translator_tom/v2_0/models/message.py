from __future__ import annotations

from typing import Annotated, ClassVar, Literal

from pydantic import ConfigDict, Field

from translator_tom.utils.object_base import TOMBase
from translator_tom.utils.shared import EdgeID
from translator_tom.v2_0.models.auxiliary_graph import (
    AuxiliaryGraph,
    AuxiliaryGraphsDict,
)
from translator_tom.v2_0.models.knowledge_graph import KnowledgeGraph
from translator_tom.v2_0.models.query_graph import QueryGraph
from translator_tom.v2_0.models.result import Result

__all__ = ["Message"]


def _mergeable_copy(other: Message) -> Message:
    """Return a copy of `other` safe to merge from / normalize without touching the original.

    Results/aux (rewritten in place by normalize, aliased in by the merge) are
    deep-copied; the KG is kept shallow, its Node/Edge objects copied on merge.
    """
    okg = other.knowledge_graph
    return Message.model_construct(
        query_graph=other.query_graph,
        knowledge_graph=(
            KnowledgeGraph.model_construct(
                nodes=dict(okg.nodes),
                edges=dict(okg.edges) if okg.edges is not None else None,
            )
            if okg is not None
            else None
        ),
        results=(
            [result.model_copy(deep=True) for result in other.results]
            if other.results is not None
            else None
        ),
        auxiliary_graphs=(
            {
                aux_id: graph.model_copy(deep=True)
                for aux_id, graph in other.auxiliary_graphs.items()
            }
            if other.auxiliary_graphs is not None
            else None
        ),
    )


class Message(TOMBase):
    """The message object holds the main content of a Query or a Response in three properties: query_graph, results, and knowledge_graph.

    The query_graph property contains the query configuration, the results
    property contains any answers that are returned by the service,
    and knowledge_graph property contains lists of edges and nodes in the
    thought graph corresponding to this message. The content of these
    properties is context-dependent to the encompassing object and
    the TRAPI operation requested.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    results: list[Result] | None = None
    """List of all returned Result objects for the query posed.

    The list SHOULD NOT be assumed to be ordered. The 'score' property,
    if present, MAY be used to infer result rankings. If Results are
    not expected (such as for a query Message), this property SHOULD
    be absent. If Results are expected (such as for a response
    Message) and no Results are available, this property SHOULD be an
    array with 0 Results in it.
    """

    query_graph: QueryGraph | None = None
    """QueryGraph object that contains a serialization of a query in the form of a graph."""

    knowledge_graph: KnowledgeGraph | None = None
    """KnowledgeGraph object that contains lists of nodes and edges in the thought graph corresponding to the message."""

    auxiliary_graphs: Annotated[AuxiliaryGraphsDict, Field(min_length=1)] | None = None
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

    def update(
        self,
        other: Message,
        pre_normalized: Literal["neither", "both", "self", "other"] = "neither",
        copy: bool = True,
    ) -> tuple[dict[EdgeID, EdgeID], dict[EdgeID, EdgeID]]:
        """Update one message in-place using the other.

        Args:
            other: The message to merge in.
            pre_normalized: Which of self/other already have normalized (hash-keyed)
                edge IDs, to skip redundant normalization.
            copy: When True (default), `other` is copied to avoid mutation. Set to False for a mild performance improvement, when safe.

        Returns:
            `(self_mapping, other_mapping)` of old:new EdgeIDs, one per side that was
            normalized (empty otherwise). Kept separate because self/other may reuse an
            old edge ID for different edges.
        """
        if self.query_graph != other.query_graph:
            raise NotImplementedError("Query graph merging not yet supported.")

        self_mapping = dict[EdgeID, EdgeID]()
        other_mapping = dict[EdgeID, EdgeID]()
        if pre_normalized in ("neither", "other"):
            self_mapping = self.normalize()
        if copy:
            other = _mergeable_copy(other)
        if pre_normalized in ("neither", "self"):
            other_mapping = other.normalize()

        if (not self.knowledge_graph) and other.knowledge_graph:
            self.knowledge_graph = (
                other.knowledge_graph.model_copy(deep=True)
                if copy
                else other.knowledge_graph
            )
        elif self.knowledge_graph and other.knowledge_graph:
            # Both KGs already normalized above; skip re-normalizing.
            self.knowledge_graph.update(
                other.knowledge_graph, pre_normalized="both", copy=copy
            )

        if (not self.results) and other.results:
            self.results = other.results
        elif self.results and other.results:
            Result.merge_results(self.results, other.results)

        if (not self.auxiliary_graphs) and other.auxiliary_graphs:
            self.auxiliary_graphs = other.auxiliary_graphs
        elif self.auxiliary_graphs and other.auxiliary_graphs:
            AuxiliaryGraph.merge_dictionaries(
                self.auxiliary_graphs, other.auxiliary_graphs
            )

        return self_mapping, other_mapping

    def normalize(self) -> dict[EdgeID, EdgeID]:
        """Normalize the knowledge_graph and update the results and auxiliary_graphs accordingly."""
        if self.knowledge_graph is None:
            return {}

        mapping = self.knowledge_graph.normalize()

        AuxiliaryGraph.normalize_aux_dict(self.auxiliary_graphs_dict, mapping)
        Result.normalize_list(self.results_list, mapping)

        return mapping

    def prune_kg(self) -> None:
        """Prune the knowledge_graph."""
        if self.knowledge_graph is None:
            return
        self.knowledge_graph.prune(self.auxiliary_graphs_dict, self.results_list)
