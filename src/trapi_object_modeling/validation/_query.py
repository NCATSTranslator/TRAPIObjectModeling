from __future__ import annotations

from typing import Any

from trapi_object_modeling.models.query import Query
from trapi_object_modeling.validation._util import (
    Location,
    SemanticValidationResult,
    extend_location,
    get_list_locations,
    semantic_validate,
    validate_many,
    validation_pipeline,
)


@semantic_validate.register(Query)
def validate_query(
    obj: Query,
    location: Location | None = None,
    **kwargs: Any,  # pyright: ignore[reportUnusedParameter]
) -> SemanticValidationResult:
    return validation_pipeline(
        semantic_validate(obj.message),
        validate_many(
            *obj.workflow_list,
            locations=get_list_locations(
                obj.workflow_list, extend_location(location, "workflow")
            ),
        ),
    )
