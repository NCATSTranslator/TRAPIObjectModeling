from __future__ import annotations

from typing_extensions import TypedDict

from translator_tom.models.shared import AuxGraphID

__all__ = ["PathBindingDict"]


class PathBindingDict(TypedDict):
    id: AuxGraphID
