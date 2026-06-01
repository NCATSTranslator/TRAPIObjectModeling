from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from translator_tom.model_dicts.attribute import AttributeDict
from translator_tom.model_dicts.qualifier import QualifierDict
from translator_tom.model_dicts.retrieval_source import RetrievalSourceDict
from translator_tom.models.shared import CURIE, EdgeID
from translator_tom.utils.biolink import Biolink

__all__ = [
    "EdgeDict",
    "KnowledgeGraphDict",
    "NodeDict",
]


class NodeDict(TypedDict):
    name: NotRequired[str | None]
    categories: list[Biolink.Entity]
    attributes: list[AttributeDict]
    is_set: NotRequired[bool | None]


class EdgeDict(TypedDict):
    predicate: Biolink.Predicate
    subject: CURIE
    object: CURIE
    attributes: NotRequired[list[AttributeDict] | None]
    qualifiers: NotRequired[list[QualifierDict] | None]
    sources: list[RetrievalSourceDict]


class KnowledgeGraphDict(TypedDict):
    nodes: dict[CURIE, NodeDict]
    edges: dict[EdgeID, EdgeDict]
