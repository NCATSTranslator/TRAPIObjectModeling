from __future__ import annotations

from typing_extensions import TypedDict

from translator_tom.model_dicts.attribute import AttributeDict
from translator_tom.models.shared import EdgeID

__all__ = ["EdgeBindingDict"]


class EdgeBindingDict(TypedDict):
    id: EdgeID
    attributes: list[AttributeDict]
