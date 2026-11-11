from __future__ import annotations

from typing_extensions import NotRequired

from translator_tom.utils.biolink import Biolink
from translator_tom.utils.dict_util_base import DictUtil, TOMBaseDict
from translator_tom.utils.shared import (
    CURIE,
    KnowledgeType,
    QEdgeID,
    QNodeID,
    QPathID,
)
from translator_tom.v2_0.model_dicts.attribute import AttributeConstraintDict
from translator_tom.v2_0.model_dicts.constraints import (
    QEdgeConstraintsDict,
    QEdgeConstraintsDictUtil,
)
from translator_tom.v2_0.model_dicts.path_constraint import PathConstraintDict
from translator_tom.v2_0.models.query_graph import (
    QEdge,
    QNode,
    QPath,
    QueryGraph,
    SetInterpretation,
)

__all__ = [
    "QEdgeDict",
    "QEdgeDictUtil",
    "QNodeDict",
    "QNodeDictUtil",
    "QPathDict",
    "QPathDictUtil",
    "QueryGraphDict",
    "QueryGraphDictUtil",
]


class QNodeDict(TOMBaseDict):
    ids: NotRequired[list[CURIE]]
    categories: NotRequired[list[Biolink.Entity]]
    set_interpretation: NotRequired[SetInterpretation]
    member_ids: NotRequired[list[CURIE]]
    constraints: NotRequired[list[AttributeConstraintDict]]


class QNodeDictUtil(DictUtil[QNodeDict]):
    """Utility methods for `QNodeDict`, mirroring those on the `QNode` model."""

    _model = QNode

    @staticmethod
    def ids_list(qnode: QNodeDict) -> list[CURIE]:
        """Get the IDs as a guaranteed list, even if they are represented as None."""
        ids = qnode.get("ids")
        return ids if ids is not None else []

    @staticmethod
    def categories_list(qnode: QNodeDict) -> list[Biolink.Entity]:
        """Get the categories as a guaranteed list, even if they are represented as None."""
        categories = qnode.get("categories")
        return categories if categories is not None else []

    @staticmethod
    def member_ids_list(qnode: QNodeDict) -> list[CURIE]:
        """Get the member_ids as a guaranteed list, even if they are represented as None."""
        member_ids = qnode.get("member_ids")
        return member_ids if member_ids is not None else []

    @staticmethod
    def constraints_list(qnode: QNodeDict) -> list[AttributeConstraintDict]:
        """Get the attribute constraints as a guaranteed list, even if they are represented as None."""
        constraints = qnode.get("constraints")
        return constraints if constraints is not None else []


class QEdgeDict(TOMBaseDict):
    knowledge_type: NotRequired[KnowledgeType]
    predicates: NotRequired[list[Biolink.Predicate]]
    subject: QNodeID
    object: QNodeID
    constraints: NotRequired[QEdgeConstraintsDict]


class QEdgeDictUtil(DictUtil[QEdgeDict]):
    """Utility methods for `QEdgeDict`, mirroring those on the `QEdge` model."""

    _model = QEdge

    @staticmethod
    def predicates_list(qedge: QEdgeDict) -> list[Biolink.Predicate]:
        """Get the predicates as a guaranteed list, even if they are represented as None."""
        predicates = qedge.get("predicates")
        return predicates if predicates is not None else []

    @staticmethod
    def get_inverse(qedge: QEdgeDict) -> QEdgeDict:
        """Get an inverse copy of the QEdge."""
        inverse_predicates = list[Biolink.Predicate]()
        failed_predicates = list[Biolink.Predicate]()
        for predicate in QEdgeDictUtil.predicates_list(qedge):
            inverse = Biolink.get_inverse(predicate)
            if inverse is None:
                failed_predicates.append(predicate)
                continue
            inverse_predicates.append(inverse)

        if len(failed_predicates) > 0:
            raise ValueError(f"Cannot invert predicates {failed_predicates}.")

        # Keep dict minimal as in model behavior.
        inverted: QEdgeDict = {
            "subject": qedge["object"],
            "object": qedge["subject"],
        }
        knowledge_type = qedge.get("knowledge_type")
        if knowledge_type is not None:
            inverted["knowledge_type"] = knowledge_type
        if inverse_predicates:
            inverted["predicates"] = inverse_predicates
        constraints = qedge.get("constraints")
        if constraints is not None:
            inverted["constraints"] = QEdgeConstraintsDictUtil.get_inverse(constraints)
        return inverted

    @staticmethod
    def get_qualifier_value(qedge: QEdgeDict, type_id: Biolink.Qualifier) -> str | None:
        """Return the value for a qualifier type from this QEdge's constraints, if present."""
        constraints = qedge.get("constraints")
        if constraints is None:
            return None
        for qualifier_set in QEdgeConstraintsDictUtil.qualifiers_list(constraints):
            if type_id in qualifier_set:
                return qualifier_set[type_id]
        return None


class QPathDict(TOMBaseDict):
    subject: QNodeID
    object: QNodeID
    predicates: NotRequired[list[Biolink.Predicate]]
    constraints: NotRequired[list[PathConstraintDict]]


class QPathDictUtil(DictUtil[QPathDict]):
    """Utility methods for `QPathDict`, mirroring those on the `QPath` model."""

    _model = QPath

    @staticmethod
    def predicates_list(qpath: QPathDict) -> list[Biolink.Predicate]:
        """Get the predicates as a guaranteed list, even if they are represented as None."""
        predicates = qpath.get("predicates")
        return predicates if predicates is not None else []

    @staticmethod
    def constraints_list(qpath: QPathDict) -> list[PathConstraintDict]:
        """Get the constraints as a guaranteed list, even if they are represented as None."""
        constraints = qpath.get("constraints")
        return constraints if constraints is not None else []


class QueryGraphDict(TOMBaseDict):
    nodes: dict[QNodeID, QNodeDict]
    edges: NotRequired[dict[QEdgeID, QEdgeDict]]
    paths: NotRequired[dict[QPathID, QPathDict]]


class QueryGraphDictUtil(DictUtil[QueryGraphDict]):
    """Utility methods for `QueryGraphDict`, mirroring those on the `QueryGraph` model."""

    _model = QueryGraph

    @staticmethod
    def edges_dict(query_graph: QueryGraphDict) -> dict[QEdgeID, QEdgeDict]:
        """Get the edges as a guaranteed dict, even if they are represented as None."""
        edges = query_graph.get("edges")
        return edges if edges is not None else {}

    @staticmethod
    def paths_dict(query_graph: QueryGraphDict) -> dict[QPathID, QPathDict]:
        """Get the paths as a guaranteed dict, even if they are represented as None."""
        paths = query_graph.get("paths")
        return paths if paths is not None else {}

    @staticmethod
    def new() -> QueryGraphDict:
        """Return an empty instance, without having to pass required containers."""
        return {"nodes": {}}

    @staticmethod
    def get_unpinned(
        query_graph: QueryGraphDict, qedge_id: QEdgeID | None = None
    ) -> list[tuple[QNodeID, QNodeDict]]:
        """Return the unpinned (answer) qnodes as (id, qnode) pairs.

        Args:
            query_graph: The query graph whose qnodes to consider.
            qedge_id: Only consider the given qedge's nodes.
        """
        nodes = query_graph["nodes"]
        if qedge_id is None:
            candidate_ids = list(nodes)
        else:
            qedge = QueryGraphDictUtil.edges_dict(query_graph)[qedge_id]
            candidate_ids = [qedge["subject"], qedge["object"]]
        return [
            (qid, qnode)
            for qid in candidate_ids
            if (qnode := nodes.get(qid)) is not None and not qnode.get("ids")
        ]
