from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from translator_tom.utils.biolink import Biolink

__all__ = ["PathConstraintDict"]


class PathConstraintDict(TypedDict):
    intermediate_categories: NotRequired[list[Biolink.Entity] | None]
