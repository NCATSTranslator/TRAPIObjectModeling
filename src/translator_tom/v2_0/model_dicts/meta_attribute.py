from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from translator_tom.utils.dict_util_base import DictUtil
from translator_tom.utils.hash import tomhash
from translator_tom.utils.shared import CURIE
from translator_tom.v2_0.models.meta_attribute import MetaAttribute

__all__ = ["MetaAttributeDict", "MetaAttributeDictUtil"]


class MetaAttributeDict(TypedDict):
    attribute_type_id: CURIE
    attribute_source: NotRequired[str | None]
    original_attribute_names: NotRequired[list[str] | None]
    constraint_use: NotRequired[bool]
    constraint_name: NotRequired[str | None]


class MetaAttributeDictUtil(DictUtil[MetaAttributeDict]):
    """Utility methods for `MetaAttributeDict`, mirroring those on the `MetaAttribute` model."""

    _model = MetaAttribute

    @staticmethod
    def original_attribute_names_list(meta_attribute: MetaAttributeDict) -> list[str]:
        """Get the original attribute names as a guaranteed list, even if they are represented as None."""
        original_attribute_names = meta_attribute.get("original_attribute_names")
        return original_attribute_names if original_attribute_names is not None else []

    @classmethod
    def hash(cls, obj: MetaAttributeDict) -> str:
        """Hash matching `MetaAttribute.hash` (identity plus constraint usability)."""
        return tomhash(
            (
                obj["attribute_type_id"],
                obj.get("attribute_source"),
                obj.get("constraint_use", cls._default("constraint_use")),
            )
        )

    @staticmethod
    def merge_attribute_lists(
        old: list[MetaAttributeDict], new: list[MetaAttributeDict]
    ) -> None:
        """Merge the new attributes into the existing attributes."""
        attrs = {MetaAttributeDictUtil.hash(attr): attr for attr in old}
        for attr in new:
            attrs[MetaAttributeDictUtil.hash(attr)] = attr

        old.clear()
        old.extend(attrs.values())
