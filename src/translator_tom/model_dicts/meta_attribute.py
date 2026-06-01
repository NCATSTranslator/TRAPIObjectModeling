from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from translator_tom.models.shared import CURIE

__all__ = ["MetaAttributeDict"]


class MetaAttributeDict(TypedDict):
    attribute_type_id: CURIE
    attribute_source: NotRequired[str | None]
    original_attribute_names: NotRequired[list[str] | None]
    constraint_use: NotRequired[bool | None]
    constraint_name: NotRequired[str | None]
