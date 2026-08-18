from __future__ import annotations

from typing import Any

from translator_tom.models.path_constraint import PathConstraint
from translator_tom.validation._util import (
    Location,
    SemanticValidationResult,
    always_valid,
    extend_location,
    semantic_validate,
    validate_category,
)


@semantic_validate.register(PathConstraint)
def _validate_path_constraint(
    obj: PathConstraint,
    location: Location | None = None,
    **_: Any,
) -> SemanticValidationResult:
    warnings, errors = always_valid()
    for category in obj.required_intermediate_categories_list:
        new_warnings, new_errors = validate_category(
            category, extend_location(location, "required_intermediate_categories")
        )
        warnings.extend(new_warnings)
        errors.extend(new_errors)
    return warnings, errors
