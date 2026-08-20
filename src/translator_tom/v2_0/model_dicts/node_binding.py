from __future__ import annotations

from typing_extensions import TypedDict

from translator_tom.utils.dict_util_base import DictUtil
from translator_tom.utils.hash import tomhash
from translator_tom.utils.shared import CURIE
from translator_tom.v2_0.models.node_binding import NodeBinding

__all__ = ["NodeBindingDict", "NodeBindingDictUtil"]


class NodeBindingDict(TypedDict):
    ids: list[CURIE]


class NodeBindingDictUtil(DictUtil[NodeBindingDict]):
    """Utility methods for `NodeBindingDict`, mirroring those on the `NodeBinding` model."""

    _model = NodeBinding

    @classmethod
    def hash(cls, obj: NodeBindingDict) -> str:
        """Hash matching `NodeBinding.hash` (unordered bound node ids)."""
        return tomhash(frozenset(obj["ids"]))
