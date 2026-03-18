from __future__ import annotations

from typing import Annotated, Any, override

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from trapi_object_modeling.shared import BiolinkEntity
from trapi_object_modeling.utils.object_base import (
    Location,
    SemanticValidationResult,
    TOMBaseObject,
)
from trapi_object_modeling.utils.semantic_validation import (
    extend_location,
    validate_category,
    validation_pipeline,
)


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

    @property
    def intermediate_categories_list(self) -> list[BiolinkEntity]:
        """Get the intermediate_categories as a guaranteed list, even if they are represented as None."""
        return (
            self.intermediate_categories
            if self.intermediate_categories is not None
            else []
        )

    @override
    def semantic_validate(
        self, location: Location | None = None, **kwargs: Any
    ) -> SemanticValidationResult:
        return validation_pipeline(
            *(
                validate_category(
                    cat, extend_location(location, "intermediate_categories")
                )
                for cat in self.intermediate_categories_list
            )
        )
