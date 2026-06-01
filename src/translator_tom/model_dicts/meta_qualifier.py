from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from translator_tom.utils.biolink import Biolink

__all__ = ["MetaQualifierDict"]


class MetaQualifierDict(TypedDict):
    qualifier_type_id: Biolink.Qualifier
    applicable_values: NotRequired[list[str] | None]
