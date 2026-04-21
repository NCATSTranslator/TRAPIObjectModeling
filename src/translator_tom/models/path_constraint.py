from __future__ import annotations

from typing import Annotated

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from translator_tom.models.shared import BiolinkEntity
from translator_tom.utils.object_base import TOMBaseObject


@dataclass(kw_only=True, config=ConfigDict(extra="allow"), eq=False)
class PathConstraint(TOMBaseObject):
    """A constraint for paths. ARAs must comply with constraints when finding paths."""

    intermediate_categories: (
        Annotated[list[BiolinkEntity], Field(min_length=1)] | None
    ) = None
    """A list of Biolink model categories by which to constrain paths returned.

    If multiple categories are listed, it should be interpreted as an AND
    relationship. Each path returned by ARAs MUST contain at least one node
    of each category listed.
    """

    @property
    def intermediate_categories_list(self) -> list[BiolinkEntity]:
        """Get the intermediate_categories as a guaranteed list, even if they are represented as None."""
        return (
            self.intermediate_categories
            if self.intermediate_categories is not None
            else []
        )
