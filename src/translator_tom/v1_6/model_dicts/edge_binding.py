from __future__ import annotations

from typing_extensions import TypedDict

from translator_tom.utils.dict_util_base import DictUtil
from translator_tom.utils.hash import tomhash
from translator_tom.utils.shared import EdgeID
from translator_tom.v1_6.model_dicts.attribute import AttributeDict, AttributeDictUtil
from translator_tom.v1_6.models.edge_binding import EdgeBinding

__all__ = ["EdgeBindingDict", "EdgeBindingDictUtil"]


class EdgeBindingDict(TypedDict):
    id: EdgeID
    attributes: list[AttributeDict]


class EdgeBindingDictUtil(DictUtil[EdgeBindingDict]):
    """Utility methods for `EdgeBindingDict`, mirroring those on the `EdgeBinding` model."""

    _model = EdgeBinding

    @classmethod
    def hash(cls, obj: EdgeBindingDict) -> str:
        """Hash matching `EdgeBinding.hash` (bound edge id plus its attributes)."""
        return tomhash(
            (obj["id"], frozenset(AttributeDictUtil.hash(a) for a in obj["attributes"]))
        )
