from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from translator_tom.utils.dict_util_base import DictUtil
from translator_tom.utils.hash import tomhash
from translator_tom.utils.shared import CURIE
from translator_tom.v1_6.model_dicts.attribute import AttributeDict, AttributeDictUtil
from translator_tom.v1_6.models.node_binding import NodeBinding

__all__ = ["NodeBindingDict", "NodeBindingDictUtil"]


class NodeBindingDict(TypedDict):
    id: CURIE
    query_id: NotRequired[CURIE | None]
    attributes: list[AttributeDict]


class NodeBindingDictUtil(DictUtil[NodeBindingDict]):
    """Utility methods for `NodeBindingDict`, mirroring those on the `NodeBinding` model."""

    _model = NodeBinding

    @classmethod
    def hash(cls, obj: NodeBindingDict) -> str:
        """Hash matching `NodeBinding.hash` (bound node id, query id, attributes)."""
        return tomhash(
            (
                obj["id"],
                obj.get("query_id"),
                frozenset(AttributeDictUtil.hash(a) for a in obj["attributes"]),
            )
        )
