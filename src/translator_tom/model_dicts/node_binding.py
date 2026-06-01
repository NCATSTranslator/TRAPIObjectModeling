from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from translator_tom.model_dicts.attribute import AttributeDict
from translator_tom.models.shared import CURIE

__all__ = ["NodeBindingDict"]


class NodeBindingDict(TypedDict):
    id: CURIE
    query_id: NotRequired[CURIE | None]
    attributes: list[AttributeDict]
