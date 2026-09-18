from __future__ import annotations

from copy import deepcopy
from typing import Literal, cast

from typing_extensions import NotRequired, TypedDict

from translator_tom.utils import set_interpretation
from translator_tom.utils.dict_util_base import DictUtil
from translator_tom.utils.set_interpretation import (
    QNodeSpec,
    QueryStamp,
    ResultStamp,
    SolvedResult,
)
from translator_tom.utils.shared import CURIE, AuxGraphID, EdgeID, QNodeID
from translator_tom.v1_6.model_dicts.auxiliary_graph import (
    AuxiliaryGraphDict,
    AuxiliaryGraphDictUtil,
    AuxiliaryGraphsDict,
)
from translator_tom.v1_6.model_dicts.knowledge_graph import (
    KnowledgeGraphDict,
    KnowledgeGraphDictUtil,
)
from translator_tom.v1_6.model_dicts.query_graph import (
    PathfinderQueryGraphDict,
    PathfinderQueryGraphDictUtil,
    QNodeDictUtil,
    QueryGraphDict,
    QueryGraphDictUtil,
)
from translator_tom.v1_6.model_dicts.result import ResultDict, ResultDictUtil
from translator_tom.v1_6.models.message import Message

__all__ = ["MessageDict", "MessageDictUtil"]


class MessageDict(TypedDict):
    results: NotRequired[list[ResultDict] | None]
    query_graph: NotRequired[QueryGraphDict | PathfinderQueryGraphDict | None]
    knowledge_graph: NotRequired[KnowledgeGraphDict | None]
    auxiliary_graphs: NotRequired[dict[AuxGraphID, AuxiliaryGraphDict] | None]


def _query_graph_hash(
    query_graph: QueryGraphDict | PathfinderQueryGraphDict | None,
) -> str | None:
    """Hash a query graph for identity comparison, ignoring extra keys (like model `==`)."""
    if query_graph is None:
        return None
    if "paths" in query_graph:
        return PathfinderQueryGraphDictUtil.hash(
            cast("PathfinderQueryGraphDict", query_graph)
        )
    return QueryGraphDictUtil.hash(query_graph)


def _mergeable_copy(other: MessageDict) -> MessageDict:
    """Return a copy of `other` safe to merge from / normalize without touching the caller's dict.

    Results/aux (rewritten in place by normalize, aliased in by the merge) are
    deep-copied; the KG is kept shallow, its node/edge dicts copied on merge.
    """
    copied: MessageDict = {}
    if "query_graph" in other:
        copied["query_graph"] = other["query_graph"]
    if other_kg := other.get("knowledge_graph"):
        copied["knowledge_graph"] = {
            "nodes": dict(other_kg["nodes"]),
            "edges": dict(other_kg["edges"]),
        }
    results = other.get("results")
    if results is not None:
        copied["results"] = deepcopy(results)
    aux = other.get("auxiliary_graphs")
    if aux is not None:
        copied["auxiliary_graphs"] = deepcopy(aux)
    return copied


class MessageDictUtil(DictUtil[MessageDict]):
    """Utility methods for `MessageDict`, mirroring those on the `Message` model."""

    _model = Message

    @staticmethod
    def results_list(message: MessageDict) -> list[ResultDict]:
        """Get the results as a guaranteed list, even if they are represented as None."""
        results = message.get("results")
        return results if results is not None else []

    @staticmethod
    def auxiliary_graphs_dict(message: MessageDict) -> AuxiliaryGraphsDict:
        """Get the auxiliary_graphs as a guaranteed dict, even if they are represented as None."""
        auxiliary_graphs = message.get("auxiliary_graphs")
        return auxiliary_graphs if auxiliary_graphs is not None else {}

    @staticmethod
    def normalize(message: MessageDict) -> dict[EdgeID, EdgeID]:
        """Normalize the knowledge_graph and update results and auxiliary_graphs accordingly."""
        knowledge_graph = message.get("knowledge_graph")
        if knowledge_graph is None:
            return {}

        mapping = KnowledgeGraphDictUtil.normalize(knowledge_graph)

        AuxiliaryGraphDictUtil.normalize_aux_dict(
            MessageDictUtil.auxiliary_graphs_dict(message), mapping
        )
        ResultDictUtil.normalize_list(MessageDictUtil.results_list(message), mapping)

        return mapping

    @staticmethod
    def update(
        message: MessageDict,
        other: MessageDict,
        pre_normalized: Literal["neither", "both", "self", "other"] = "neither",
        copy: bool = True,
    ) -> tuple[dict[EdgeID, EdgeID], dict[EdgeID, EdgeID]]:
        """Update one message in-place using the other.

        Args:
            message: The message to update.
            other: The message to merge in.
            pre_normalized: Which of message/other already have normalized (hash-keyed)
                edge IDs, to skip redundant normalization.
            copy: When True (default), `other` is copied to avoid mutation. Set to False for a mild performance improvement, when safe.

        Returns:
            `(message_mapping, other_mapping)` of old:new EdgeIDs, one per side that was
            normalized (empty otherwise). Kept separate because the two may reuse an old
            edge ID for different edges.
        """
        # Compare by hash (like the model's `==`) so extra/non-schema keys are ignored.
        if _query_graph_hash(message.get("query_graph")) != _query_graph_hash(
            other.get("query_graph")
        ):
            raise NotImplementedError("Query graph merging not yet supported.")

        self_mapping = dict[EdgeID, EdgeID]()
        other_mapping = dict[EdgeID, EdgeID]()
        if pre_normalized in ("neither", "other"):
            self_mapping = MessageDictUtil.normalize(message)
        if copy:
            other = _mergeable_copy(other)
        if pre_normalized in ("neither", "self"):
            other_mapping = MessageDictUtil.normalize(other)

        msg_kg = message.get("knowledge_graph")
        other_kg = other.get("knowledge_graph")
        if (not msg_kg) and other_kg:
            message["knowledge_graph"] = deepcopy(other_kg) if copy else other_kg
        elif msg_kg and other_kg:
            # Both KGs already normalized above; skip re-normalizing.
            KnowledgeGraphDictUtil.update(
                msg_kg, other_kg, pre_normalized="both", copy=copy
            )

        msg_results = message.get("results")
        other_results = other.get("results")
        if (not msg_results) and other_results:
            message["results"] = other_results
        elif msg_results and other_results:
            ResultDictUtil.merge_results(msg_results, other_results)

        msg_aux = message.get("auxiliary_graphs")
        other_aux = other.get("auxiliary_graphs")
        if (not msg_aux) and other_aux:
            message["auxiliary_graphs"] = other_aux
        elif msg_aux and other_aux:
            AuxiliaryGraphDictUtil.merge_dictionaries(msg_aux, other_aux)

        return self_mapping, other_mapping

    @staticmethod
    def prune_kg(message: MessageDict) -> None:
        """Prune the knowledge_graph."""
        knowledge_graph = message.get("knowledge_graph")
        if knowledge_graph is None:
            return
        KnowledgeGraphDictUtil.prune(
            knowledge_graph,
            MessageDictUtil.auxiliary_graphs_dict(message),
            MessageDictUtil.results_list(message),
        )

    @staticmethod
    def solve_set_interpretation(
        message: MessageDict, *, skip_many: bool = False
    ) -> None:
        """Rewrite `results` in place to obey each QNode's set_interpretation.

        Mirrors `Message.solve_set_interpretation`.
        Each input Result must be an expanded (one knode per qnode), valid query-graph match.
        Connectivity is inferred from node bindings + qedge topology.

        BATCH keys the grouping.
        ALL binds its set node; every member must be edge-connected to its
        neighbors, else the batch-group is dropped.
        TRAPI 1.6 has no COLLATE.
        The knowledge_graph is left untouched -- call `prune_kg` afterward.

        Args:
            message: The message to solve in place.
            skip_many: Treat MANY nodes as BATCH instead of raising.
        """
        query_graph = message.get("query_graph")
        results = message.get("results")
        if query_graph is None or not results:
            return

        query = MessageDictUtil._stamp_query(query_graph)
        result_stamps = MessageDictUtil._stamp_results(results)
        kg = message.get("knowledge_graph")
        kg_node_ids = kg["nodes"].keys() if kg else ()
        solved_results = set_interpretation.solve(
            query, result_stamps, kg_node_ids, skip_many=skip_many
        )
        message["results"] = [
            MessageDictUtil._materialize(results, solved_result)
            for solved_result in solved_results
        ]

    @staticmethod
    def _stamp_query(
        query_graph: QueryGraphDict | PathfinderQueryGraphDict,
    ) -> QueryStamp:
        """Stamp the query graph into the plain-string form `solve` operates on.

        Args:
            query_graph: The query graph to stamp (Pathfinder has no qedges).

        Returns:
            The `QueryStamp` (each QNode's `QNodeSpec`, and qedge `(subject, object)`).
        """
        nodes = {
            qnode_id: QNodeSpec(
                qnode.get("set_interpretation") or "BATCH",
                QNodeDictUtil.ids_list(qnode),
                QNodeDictUtil.member_ids_list(qnode),
            )
            for qnode_id, qnode in query_graph["nodes"].items()
        }
        edges = query_graph.get("edges") or {}
        qedges = {
            qedge_id: (qedge["subject"], qedge["object"])
            for qedge_id, qedge in edges.items()
        }
        return QueryStamp(nodes, qedges)

    @staticmethod
    def _stamp_results(results: list[ResultDict]) -> list[ResultStamp]:
        """Stamp each Result into a `ResultStamp` (enforcing the contract).

        Args:
            results: The results to stamp.

        Returns:
            One `ResultStamp` per input Result, aligned to `results`.
        """
        stamps = list[ResultStamp]()
        for result in results:
            stamp = dict[QNodeID, CURIE]()
            for qnode_id, bindings in result["node_bindings"].items():
                if len(bindings) != 1:
                    raise ValueError(
                        "solve_set_interpretation requires expanded results (one knode per QNode); "
                        f"a result binds '{qnode_id}' with {len(bindings)} node bindings."
                    )
                stamp[qnode_id] = bindings[0]["id"]
            stamps.append(stamp)
        return stamps

    @staticmethod
    def _materialize(
        results: list[ResultDict], solved_result: SolvedResult
    ) -> ResultDict:
        """Build a Result from the backing results and the solved set-node bindings.

        Args:
            results: The full result list (indexed by `solved_result.backing_indices`).
            solved_result: One solved result (set-node bindings + backing indices).

        Returns:
            One merged Result with ALL bindings applied.
        """
        backing_results = [results[index] for index in solved_result.backing_indices]
        if len(backing_results) == 1:
            # Single backing: no merge, so shallow-copy and rewrite only node_bindings
            first = backing_results[0]
            base = cast(
                ResultDict, {**first, "node_bindings": {**first["node_bindings"]}}
            )
        else:
            base = deepcopy(backing_results[0])
            for other in backing_results[1:]:
                ResultDictUtil.update(base, other)

        for qnode_id, ids in solved_result.set_bindings.items():
            base["node_bindings"][qnode_id] = [
                {"id": knode, "attributes": []} for knode in ids
            ]
        return base
