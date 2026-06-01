from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from translator_tom.model_dicts.meta_attribute import MetaAttributeDict
from translator_tom.model_dicts.meta_qualifier import MetaQualifierDict
from translator_tom.models.shared import KnowledgeType
from translator_tom.utils.biolink import Biolink

__all__ = [
    "MetaEdgeDict",
    "MetaKnowledgeGraphDict",
    "MetaNodeDict",
]


class MetaNodeDict(TypedDict):
    id_prefixes: list[str]
    attributes: NotRequired[list[MetaAttributeDict] | None]


class MetaEdgeDict(TypedDict):
    subject: Biolink.Entity
    predicate: Biolink.Predicate
    object: Biolink.Entity
    knowledge_types: NotRequired[list[KnowledgeType] | None]
    attributes: NotRequired[list[MetaAttributeDict] | None]
    qualifiers: NotRequired[list[MetaQualifierDict] | None]
    association: NotRequired[Biolink.Entity | None]


class MetaKnowledgeGraphDict(TypedDict):
    nodes: dict[Biolink.Entity, MetaNodeDict]
    edges: list[MetaEdgeDict]
