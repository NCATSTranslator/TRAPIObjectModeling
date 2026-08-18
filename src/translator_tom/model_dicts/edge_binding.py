from __future__ import annotations

from typing_extensions import TypedDict

from translator_tom.models.edge_binding import EdgeBinding
from translator_tom.models.shared import EdgeID
from translator_tom.utils.dict_util_base import DictUtil
from translator_tom.utils.hash import tomhash

__all__ = ["EdgeBindingDict", "EdgeBindingDictUtil"]


class EdgeBindingDict(TypedDict):
    ids: list[EdgeID]


class EdgeBindingDictUtil(DictUtil[EdgeBindingDict]):
    """Utility methods for `EdgeBindingDict`, mirroring those on the `EdgeBinding` model."""

    _model = EdgeBinding

    @classmethod
    def hash(cls, obj: EdgeBindingDict) -> str:
        """Hash matching `EdgeBinding.hash` (unordered bound edge ids)."""
        return tomhash(frozenset(obj["ids"]))
