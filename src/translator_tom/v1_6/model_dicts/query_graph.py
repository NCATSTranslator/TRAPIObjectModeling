from __future__ import annotations

from collections.abc import Mapping

from typing_extensions import NotRequired

from translator_tom.utils.biolink import Biolink
from translator_tom.utils.dict_util_base import (
    DictUtil,
    TOMBaseDict,
    register_union_discriminator,
)
from translator_tom.utils.shared import (
    CURIE,
    KnowledgeType,
    QEdgeID,
    QNodeID,
    QPathID,
)
from translator_tom.v1_6.model_dicts.attribute import (
    AttributeConstraintDict,
    AttributeConstraintDictUtil,
)
from translator_tom.v1_6.model_dicts.path_constraint import PathConstraintDict
from translator_tom.v1_6.model_dicts.qualifier import (
    QualifierConstraintDict,
    QualifierConstraintDictUtil,
)
from translator_tom.v1_6.models.query_graph import (
    PathfinderQueryGraph,
    QEdge,
    QNode,
    QPath,
    QueryGraph,
    SetInterpretation,
)

__all__ = [
    "BaseQueryGraphDict",
    "PathfinderQueryGraphDict",
    "PathfinderQueryGraphDictUtil",
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
    ids: NotRequired[list[CURIE] | None]
    categories: NotRequired[list[Biolink.Entity] | None]
    set_interpretation: NotRequired[SetInterpretation | None]
    member_ids: NotRequired[list[CURIE] | None]
    constraints: NotRequired[list[AttributeConstraintDict] | None]


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
    knowledge_type: NotRequired[KnowledgeType | None]
    predicates: NotRequired[list[Biolink.Predicate] | None]
    subject: QNodeID
    object: QNodeID
    attribute_constraints: NotRequired[list[AttributeConstraintDict] | None]
    qualifier_constraints: NotRequired[list[QualifierConstraintDict] | None]


class QEdgeDictUtil(DictUtil[QEdgeDict]):
    """Utility methods for `QEdgeDict`, mirroring those on the `QEdge` model."""

    _model = QEdge

    @staticmethod
    def predicates_list(qedge: QEdgeDict) -> list[Biolink.Predicate]:
        """Get the predicates as a guaranteed list, even if they are represented as None."""
        predicates = qedge.get("predicates")
        return predicates if predicates is not None else []

    @staticmethod
    def attribute_constraints_list(qedge: QEdgeDict) -> list[AttributeConstraintDict]:
        """Get the attribute_constraints as a guaranteed list, even if they are represented as None."""
        attribute_constraints = qedge.get("attribute_constraints")
        return attribute_constraints if attribute_constraints is not None else []

    @staticmethod
    def qualifier_constraints_list(qedge: QEdgeDict) -> list[QualifierConstraintDict]:
        """Get the qualifier_constraints as a guaranteed list, even if they are represented as None."""
        qualifier_constraints = qedge.get("qualifier_constraints")
        return qualifier_constraints if qualifier_constraints is not None else []

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

        # Keep dict minimal as in model behavior
        inverted: QEdgeDict = {
            "subject": qedge["object"],
            "object": qedge["subject"],
        }
        knowledge_type = qedge.get("knowledge_type")
        if knowledge_type is not None:
            inverted["knowledge_type"] = knowledge_type
        if inverse_predicates:
            inverted["predicates"] = inverse_predicates
        inverse_attribute_constraints = [
            AttributeConstraintDictUtil.get_inverse(ac)
            for ac in QEdgeDictUtil.attribute_constraints_list(qedge)
        ]
        if inverse_attribute_constraints:
            inverted["attribute_constraints"] = inverse_attribute_constraints
        inverse_qualifier_constraints = [
            QualifierConstraintDictUtil.get_inverse(qc)
            for qc in QEdgeDictUtil.qualifier_constraints_list(qedge)
        ]
        if inverse_qualifier_constraints:
            inverted["qualifier_constraints"] = inverse_qualifier_constraints
        return inverted

    @staticmethod
    def get_qualifier_value(qedge: QEdgeDict, type_id: Biolink.Qualifier) -> str | None:
        """Return the value for a qualifier type from this QEdge's qualifier constraints, if present."""
        for constraint in QEdgeDictUtil.qualifier_constraints_list(qedge):
            for qualifier in constraint["qualifier_set"]:
                if qualifier["qualifier_type_id"] == type_id:
                    return qualifier["qualifier_value"]
        return None


class QPathDict(TOMBaseDict):
    subject: QNodeID
    object: QNodeID
    predicates: NotRequired[list[Biolink.Predicate] | None]
    constraints: NotRequired[list[PathConstraintDict] | None]


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


class BaseQueryGraphDict(TOMBaseDict):
    nodes: dict[QNodeID, QNodeDict]


class QueryGraphDict(BaseQueryGraphDict):
    edges: dict[QEdgeID, QEdgeDict]


class QueryGraphDictUtil(DictUtil[QueryGraphDict]):
    """Utility methods for `QueryGraphDict`, mirroring those on the `QueryGraph` model."""

    _model = QueryGraph

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
            qedge = query_graph["edges"][qedge_id]
            candidate_ids = [qedge["subject"], qedge["object"]]
        return [
            (qid, qnode)
            for qid in candidate_ids
            if (qnode := nodes.get(qid)) is not None and not qnode.get("ids")
        ]


class PathfinderQueryGraphDict(BaseQueryGraphDict):
    paths: dict[QPathID, QPathDict]


class PathfinderQueryGraphDictUtil(DictUtil[PathfinderQueryGraphDict]):
    """Registration-only util for `PathfinderQueryGraphDict`."""

    _model = PathfinderQueryGraph


def _discriminate_query_graph(
    value: Mapping[str, object],
) -> type[QueryGraph | PathfinderQueryGraph]:
    """Pick the concrete query-graph model for a raw dict (`paths` -> Pathfinder)."""
    return PathfinderQueryGraph if "paths" in value else QueryGraph


# Message.query_graph is a union QueryGraph | PathfinderQueryGraph, requires explicit discriminator
register_union_discriminator(
    (QueryGraph, PathfinderQueryGraph), _discriminate_query_graph
)
