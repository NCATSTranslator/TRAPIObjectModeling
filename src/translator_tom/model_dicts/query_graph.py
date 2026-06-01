from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from translator_tom.model_dicts.attribute import AttributeConstraintDict
from translator_tom.model_dicts.path_constraint import PathConstraintDict
from translator_tom.model_dicts.qualifier import QualifierConstraintDict
from translator_tom.models.query_graph import SetInterpretation
from translator_tom.models.shared import (
    CURIE,
    KnowledgeType,
    QEdgeID,
    QNodeID,
    QPathID,
)
from translator_tom.utils.biolink import Biolink

__all__ = [
    "BaseQueryGraphDict",
    "PathfinderQueryGraphDict",
    "QEdgeDict",
    "QNodeDict",
    "QPathDict",
    "QueryGraphDict",
]


class QNodeDict(TypedDict):
    ids: NotRequired[list[CURIE] | None]
    categories: NotRequired[list[Biolink.Entity] | None]
    set_interpretation: NotRequired[SetInterpretation | None]
    member_ids: NotRequired[list[CURIE] | None]
    constraints: NotRequired[list[AttributeConstraintDict] | None]


class QEdgeDict(TypedDict):
    knowledge_type: NotRequired[KnowledgeType | None]
    predicates: NotRequired[list[Biolink.Predicate] | None]
    subject: QNodeID
    object: QNodeID
    attribute_constraints: NotRequired[list[AttributeConstraintDict] | None]
    qualifier_constraints: NotRequired[list[QualifierConstraintDict] | None]


class QPathDict(TypedDict):
    subject: QNodeID
    object: QNodeID
    predicates: NotRequired[list[Biolink.Predicate] | None]
    constraints: NotRequired[list[PathConstraintDict] | None]


class BaseQueryGraphDict(TypedDict):
    nodes: dict[QNodeID, QNodeDict]


class QueryGraphDict(BaseQueryGraphDict):
    edges: dict[QEdgeID, QEdgeDict]


class PathfinderQueryGraphDict(BaseQueryGraphDict):
    paths: dict[QPathID, QPathDict]
