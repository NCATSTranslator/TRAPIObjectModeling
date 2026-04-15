from __future__ import annotations

from typing import Any

from trapi_object_modeling.path_constraint import PathConstraint
from trapi_object_modeling.validation._util import (
    Location,
    SemanticValidationResult,
    extend_location,
    semantic_validate,
    validate_category,
    validation_pipeline,
)


@semantic_validate.register(PathConstraint)
def _validate_path_constraint(  # pyright: ignore[reportUnusedFunction]
    obj: PathConstraint,
    location: Location | None = None,
    **kwargs: Any,  # pyright: ignore[reportUnusedParameter]
) -> SemanticValidationResult:
    return validation_pipeline(
        *(
            validate_category(cat, extend_location(location, "intermediate_categories"))
            for cat in obj.intermediate_categories_list
        )
    )
