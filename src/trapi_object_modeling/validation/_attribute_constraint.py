from __future__ import annotations

import re
from typing import Any

from trapi_object_modeling.attribute_constraint import AttributeConstraint
from trapi_object_modeling.validation._util import (
    Location,
    SemanticValidationError,
    SemanticValidationErrorList,
    SemanticValidationResult,
    SemanticValidationWarning,
    SemanticValidationWarningList,
    extend_location,
    semantic_validate,
)


@semantic_validate.register(AttributeConstraint)
def _validate_attribute_constraint(  # pyright: ignore[reportUnusedFunction]
    obj: AttributeConstraint,
    location: Location | None = None,
    **kwargs: Any,  # pyright: ignore[reportUnusedParameter]
) -> SemanticValidationResult:
    warnings, errors = (
        SemanticValidationWarningList(),
        SemanticValidationErrorList(),
    )

    values = obj.value if isinstance(obj.value, list) else [obj.value]
    value_location = extend_location(location, "value")

    if obj.operator in (">", "<"):
        bad = next((v for v in values if not isinstance(v, int | float)), None)
        if bad is not None:
            errors.append(
                SemanticValidationError(
                    f"Operator `{obj.operator}` requires numeric value, got {type(bad).__name__}.",
                    value_location,
                )
            )

    elif obj.operator == "matches":
        for v in values:
            if not isinstance(v, str):
                errors.append(
                    SemanticValidationError(
                        f"Operator `matches` requires string value, got {type(v).__name__}.",
                        value_location,
                    )
                )
                break
            try:
                re.compile(v)
            except re.error as e:
                errors.append(
                    SemanticValidationError(
                        f"Value `{v}` is not a valid regex: {e}.",
                        value_location,
                    )
                )

    if (obj.unit_id is None) != (obj.unit_name is None):
        present = "unit_name" if obj.unit_name is not None else "unit_id"
        warnings.append(
            SemanticValidationWarning(
                "unit_id and unit_name SHOULD both be present.",
                extend_location(location, present),
            )
        )

    return warnings, errors
