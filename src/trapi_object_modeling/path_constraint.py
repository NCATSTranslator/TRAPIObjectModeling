from __future__ import annotations

from typing import Annotated

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from trapi_object_modeling.shared import BiolinkEntity
from trapi_object_modeling.utils.object_base import TOMBaseObject


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
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
