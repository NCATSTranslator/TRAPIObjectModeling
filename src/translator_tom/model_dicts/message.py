from __future__ import annotations

from copy import deepcopy
from typing import Literal

from typing_extensions import NotRequired, TypedDict

from translator_tom.model_dicts.auxiliary_graph import (
    AuxiliaryGraphDict,
    AuxiliaryGraphDictUtil,
    AuxiliaryGraphsDict,
)
from translator_tom.model_dicts.knowledge_graph import (
    KnowledgeGraphDict,
    KnowledgeGraphDictUtil,
)
from translator_tom.model_dicts.query_graph import (
    QueryGraphDict,
    QueryGraphDictUtil,
)
from translator_tom.model_dicts.result import ResultDict, ResultDictUtil
from translator_tom.models.message import Message
from translator_tom.models.shared import AuxGraphID, EdgeID
from translator_tom.utils.dict_util_base import DictUtil

__all__ = ["MessageDict", "MessageDictUtil"]


class MessageDict(TypedDict):
    results: NotRequired[list[ResultDict] | None]
    query_graph: NotRequired[QueryGraphDict | None]
    knowledge_graph: NotRequired[KnowledgeGraphDict | None]
    auxiliary_graphs: NotRequired[dict[AuxGraphID, AuxiliaryGraphDict] | None]


def _query_graph_hash(query_graph: QueryGraphDict | None) -> str | None:
    """Hash a query graph for identity comparison, ignoring extra keys (like model `==`)."""
    if query_graph is None:
        return None
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
        kg_copy: KnowledgeGraphDict = {"nodes": dict(other_kg["nodes"])}
        other_kg_edges = other_kg.get("edges")
        if other_kg_edges is not None:
            kg_copy["edges"] = dict(other_kg_edges)
        copied["knowledge_graph"] = kg_copy
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
