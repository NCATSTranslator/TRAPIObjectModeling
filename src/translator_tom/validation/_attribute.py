from __future__ import annotations

from typing import Any

from translator_tom.models.attribute import Attribute
from translator_tom.validation._util import (
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
