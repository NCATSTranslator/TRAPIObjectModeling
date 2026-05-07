from __future__ import annotations

from typing import Any

from translator_tom.models.asyncquery import (
    AsyncQuery,
    AsyncQueryStatusResponse,
)
from translator_tom.validation._query import validate_query
from translator_tom.validation._util import (
    Location,
    SemanticValidationResult,
    always_valid,
    extend_location,
    semantic_validate,
    validate_url,
    validation_pipeline,
)


@semantic_validate.register(AsyncQuery)
def _validate_async_query(
    obj: AsyncQuery,
    location: Location | None = None,
    **_: Any,
) -> SemanticValidationResult:
    return validation_pipeline(
        validate_query(obj, location),
        validate_url(obj.callback, location=extend_location(location, "callback")),
    )


@semantic_validate.register(AsyncQueryStatusResponse)
def _validate_async_query_status_response(
    obj: AsyncQueryStatusResponse,
    location: Location | None = None,
    **_: Any,
) -> SemanticValidationResult:
    if obj.response_url is not None:
        return validate_url(
            obj.response_url, location=extend_location(location, "callback")
        )
    return always_valid()
