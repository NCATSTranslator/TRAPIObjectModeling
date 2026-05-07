from __future__ import annotations

from typing import Any

from translator_tom.models.path_constraint import PathConstraint
from translator_tom.validation._util import (
    Location,
    SemanticValidationResult,
    extend_location,
    semantic_validate,
    validate_category,
    validation_pipeline,
)


@semantic_validate.register(PathConstraint)
def _validate_path_constraint(
    obj: PathConstraint,
    location: Location | None = None,
    **_: Any,
) -> SemanticValidationResult:
    return validation_pipeline(
        *(
            validate_category(cat, extend_location(location, "intermediate_categories"))
            for cat in obj.intermediate_categories_list
        )
    )
