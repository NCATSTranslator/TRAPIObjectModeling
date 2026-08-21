from __future__ import annotations

from typing import Annotated

from pydantic import Field

from translator_tom.utils.biolink import Biolink
from translator_tom.utils.object_base import TOMBase

__all__ = ["PathConstraint"]


class PathConstraint(TOMBase):
    """A constraint for paths. ARAs must comply with constraints when finding paths."""

    required_intermediate_categories: (
        Annotated[list[Biolink.Entity], Field(min_length=1)] | None
    ) = None
    """A list of Biolink Model categories by which to constrain paths returned.

    If multiple categories are listed, it should be interpreted as an AND
    relationship. Each path returned by ARAs MUST contain at least one node
    of each category listed.
    """

    @property
    def required_intermediate_categories_list(self) -> list[Biolink.Entity]:
        """Get the required_intermediate_categories as a guaranteed list, even if they are represented as None."""
        return (
            self.required_intermediate_categories
            if self.required_intermediate_categories is not None
            else []
        )
