from __future__ import annotations

from typing import Annotated, ClassVar, Literal

from pydantic import ConfigDict, Field

from translator_tom.utils import set_interpretation
from translator_tom.utils.object_base import TOMBase
from translator_tom.utils.set_interpretation import (
    QNodeSpec,
    QueryStamp,
    ResultStamp,
    SolvedResult,
)
from translator_tom.utils.shared import CURIE, EdgeID, QNodeID
from translator_tom.v2_0.models.auxiliary_graph import (
    AuxiliaryGraph,
    AuxiliaryGraphsDict,
)
from translator_tom.v2_0.models.knowledge_graph import KnowledgeGraph
from translator_tom.v2_0.models.node_binding import NodeBinding
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

    def solve_set_interpretation(
        self,
        *,
        skip_many: bool = False,
        max_collate_candidates: int = 64,
        max_collate_cliques: int = 4096,
    ) -> None:
        """Rewrite `results` in place to obey each QNode's set_interpretation.

        Each input Result must be an expanded (one knode per qnode), valid query-graph match.
        Connectivity is inferred from node bindings + qedge topology.

        BATCH keys the grouping.
        ALL binds its set node; every member must be edge-connected to its
        neighbors, else the batch-group is dropped.
        COLLATE binds every node edge-connected to its neighbors; adjacent
        COLLATE nodes must be complete-multipartite and split into maximal groups
        (multiple results).
        The knowledge_graph is left untouched -- call `prune_kg()` afterward.

        Args:
            skip_many: Treat MANY nodes as BATCH instead of raising.
            max_collate_candidates: Reject (raise `ValueError`) an adjacent-COLLATE
                component with more candidates than this -- a cheap guard before
                enumeration (0 rejects any adjacent COLLATE, a negative value
                disables it), which additionally raises past `max_collate_cliques`.
            max_collate_cliques: Reject (raise `ValueError`) an adjacent-COLLATE
                component enumerating more maximal cliques than this (a negative
                value disables it).
        """
        if self.query_graph is None or not self.results:
            return

        query = self._stamp_query(self.query_graph)
        result_stamps = self._stamp_results(self.results)
        kg_node_ids = self.knowledge_graph.nodes.keys() if self.knowledge_graph else ()
        solved_results = set_interpretation.solve(
            query,
            result_stamps,
            kg_node_ids,
            skip_many=skip_many,
            max_collate_candidates=max_collate_candidates,
            max_collate_cliques=max_collate_cliques,
        )
        self.results = [
            self._materialize(self.results, solved_result)
            for solved_result in solved_results
        ]

    @staticmethod
    def _stamp_query(query_graph: QueryGraph) -> QueryStamp:
        """Stamp the query graph into the plain-string form `solve` operates on.

        Args:
            query_graph: The query graph to stamp.

        Returns:
            The `QueryStamp` (each QNode's `QNodeSpec`, and qedge `(subject, object)`).
        """
        nodes = {
            qnode_id: QNodeSpec(
                qnode.set_interpretation or "BATCH",
                qnode.ids_list,
                qnode.member_ids_list,
            )
            for qnode_id, qnode in query_graph.nodes.items()
        }
        qedges = {
            qedge_id: (qedge.subject, qedge.object)
            for qedge_id, qedge in query_graph.edges_dict.items()
        }
        return QueryStamp(nodes, qedges)

    @staticmethod
    def _stamp_results(results: list[Result]) -> list[ResultStamp]:
        """Stamp each Result into a `ResultStamp` (enforcing the contract).

        Args:
            results: The results to stamp.

        Returns:
            One `ResultStamp` per input Result, aligned to `results`.
        """
        stamps = list[ResultStamp]()
        for result in results:
            stamp = dict[QNodeID, CURIE]()
            for qnode_id, binding in result.node_bindings.items():
                if len(binding.ids) != 1:
                    raise ValueError(
                        "solve_set_interpretation requires expanded results (one knode per QNode); "
                        f"a result binds '{qnode_id}' to {len(binding.ids)} ids."
                    )
                stamp[qnode_id] = binding.ids[0]
            stamps.append(stamp)
        return stamps

    @staticmethod
    def _materialize(results: list[Result], solved_result: SolvedResult) -> Result:
        """Build a Result from the backing results and the solved set-node bindings.

        Args:
            results: The full result list (indexed by `solved_result.backing_indices`).
            solved_result: One solved result (set-node bindings + backing indices).

        Returns:
            One merged Result with ALL/COLLATE bindings applied.
        """
        backing_results = [results[index] for index in solved_result.backing_indices]
        if len(backing_results) == 1:
            # Single backing: no merge, so shallow-copy and rewrite only node_bindings
            first = backing_results[0]
            base = first.model_copy(update={"node_bindings": dict(first.node_bindings)})
        else:
            base = backing_results[0].model_copy(deep=True)
            for other in backing_results[1:]:
                base.update(other)

        for qnode_id, ids in solved_result.set_bindings.items():
            base.node_bindings[qnode_id] = NodeBinding(ids=ids)
        return base
