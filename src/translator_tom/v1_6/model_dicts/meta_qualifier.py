from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from translator_tom.utils.biolink import Biolink
from translator_tom.utils.dict_util_base import DictUtil
from translator_tom.v1_6.models.meta_qualifier import MetaQualifier

__all__ = ["MetaQualifierDict", "MetaQualifierDictUtil"]


class MetaQualifierDict(TypedDict):
    qualifier_type_id: Biolink.Qualifier
    applicable_values: NotRequired[list[str] | None]


class MetaQualifierDictUtil(DictUtil[MetaQualifierDict]):
    """Utility methods for `MetaQualifierDict`, mirroring those on the `MetaQualifier` model."""

    _model = MetaQualifier

    @staticmethod
    def applicable_values_list(meta_qualifier: MetaQualifierDict) -> list[str]:
        """Get the applicable values as a guaranteed list, even if they are represented as None."""
        applicable_values = meta_qualifier.get("applicable_values")
        return applicable_values if applicable_values is not None else []
