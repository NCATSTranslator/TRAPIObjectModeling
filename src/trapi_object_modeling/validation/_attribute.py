from __future__ import annotations

from typing import Any

from trapi_object_modeling.models.attribute import Attribute
from trapi_object_modeling.validation._util import (
    Location,
    SemanticValidationErrorList,
    SemanticValidationResult,
    SemanticValidationWarningList,
    extend_location,
    get_list_locations,
    semantic_validate,
    validate_many,
    validate_url,
    validation_pipeline,
)


@semantic_validate.register(Attribute)
def _validate_attribute(  # pyright: ignore[reportUnusedFunction]
    obj: Attribute,
    location: Location | None = None,
    **kwargs: Any,  # pyright: ignore[reportUnusedParameter]
) -> SemanticValidationResult:
    warnings, errors = (
        SemanticValidationWarningList(),
        SemanticValidationErrorList(),
    )

    if obj.value_url is not None:
        _, new_err = validate_url(obj.value_url, extend_location(location, "value_url"))
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
