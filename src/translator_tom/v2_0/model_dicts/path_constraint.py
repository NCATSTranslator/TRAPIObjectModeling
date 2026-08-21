from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from translator_tom.utils.biolink import Biolink
from translator_tom.utils.dict_util_base import DictUtil
from translator_tom.v2_0.models.path_constraint import PathConstraint

__all__ = ["PathConstraintDict", "PathConstraintDictUtil"]


class PathConstraintDict(TypedDict):
    required_intermediate_categories: NotRequired[list[Biolink.Entity] | None]


class PathConstraintDictUtil(DictUtil[PathConstraintDict]):
    """Utility methods for `PathConstraintDict`, mirroring those on the `PathConstraint` model."""

    _model = PathConstraint

    @staticmethod
    def required_intermediate_categories_list(
        path_constraint: PathConstraintDict,
    ) -> list[Biolink.Entity]:
        """Get the required_intermediate_categories as a guaranteed list, even if they are represented as None."""
        required_intermediate_categories = path_constraint.get(
            "required_intermediate_categories"
        )
        return (
            required_intermediate_categories
            if required_intermediate_categories is not None
            else []
        )
