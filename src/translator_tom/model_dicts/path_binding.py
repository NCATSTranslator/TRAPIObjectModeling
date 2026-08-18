from __future__ import annotations

from typing_extensions import TypedDict

from translator_tom.models.path_binding import PathBinding
from translator_tom.models.shared import AuxGraphID
from translator_tom.utils.dict_util_base import DictUtil
from translator_tom.utils.hash import tomhash

__all__ = ["PathBindingDict", "PathBindingDictUtil"]


class PathBindingDict(TypedDict):
    ids: list[AuxGraphID]


class PathBindingDictUtil(DictUtil[PathBindingDict]):
    """Utility methods for `PathBindingDict`, mirroring those on the `PathBinding` model."""

    _model = PathBinding

    @classmethod
    def hash(cls, obj: PathBindingDict) -> str:
        """Hash matching `PathBinding.hash` (unordered auxiliary graph ids)."""
        return tomhash(frozenset(obj["ids"]))
