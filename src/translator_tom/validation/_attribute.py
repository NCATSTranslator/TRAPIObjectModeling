from __future__ import annotations

import re
from typing import Any

from translator_tom.models.attribute import Attribute, AttributeConstraint
from translator_tom.validation._util import (
    Location,
    SemanticValidationError,
    SemanticValidationErrorList,
    SemanticValidationResult,
    SemanticValidationWarning,
    SemanticValidationWarningList,
    extend_location,
    get_list_locations,
    semantic_validate,
    validate_many,
    validate_url,
    validation_pipeline,
)


@semantic_validate.register(Attribute)
def _validate_attribute(
    obj: Attribute,
    location: Location | None = None,
    **_: Any,
) -> SemanticValidationResult:
    warnings, errors = (
        SemanticValidationWarningList(),
        SemanticValidationErrorList(),
    )

    if obj.value_url is not None:
        _new_warn, new_err = validate_url(
            obj.value_url, extend_location(location, "value_url")
        )
        errors.extend(new_err)

    return validation_pipeline(
        (warnings, errors),
        validate_many(
            *obj.attributes_list,
            locations=get_list_locations(
                obj.attributes_list, extend_location(location, "attributes")
            ),
        ),
    )


@semantic_validate.register(AttributeConstraint)
def _validate_attribute_constraint(
    obj: AttributeConstraint,
    location: Location | None = None,
    **_: Any,
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
