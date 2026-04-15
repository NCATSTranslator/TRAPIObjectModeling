from __future__ import annotations

from typing import Any

from trapi_object_modeling.asyncquery import (
    AsyncQuery,
    AsyncQueryStatusResponse,
)
from trapi_object_modeling.validation._query import validate_query
from trapi_object_modeling.validation._util import (
    Location,
    SemanticValidationResult,
    always_valid,
    extend_location,
    semantic_validate,
    validate_url,
    validation_pipeline,
)


@semantic_validate.register(AsyncQuery)
def _validate_async_query(  # pyright: ignore[reportUnusedFunction]
    obj: AsyncQuery, location: Location | None = None, **kwargs: Any
) -> SemanticValidationResult:
    return validation_pipeline(
        validate_query(obj, location, **kwargs),
        validate_url(obj.callback, location=extend_location(location, "callback")),
    )


@semantic_validate.register(AsyncQueryStatusResponse)
def _validate_async_query_status_response(  # pyright: ignore[reportUnusedFunction]
    obj: AsyncQueryStatusResponse,
    location: Location | None = None,
    **kwargs: Any,  # pyright: ignore[reportUnusedParameter]
) -> SemanticValidationResult:
    if obj.response_url is not None:
        return validate_url(
            obj.response_url, location=extend_location(location, "callback")
        )
    return always_valid()
