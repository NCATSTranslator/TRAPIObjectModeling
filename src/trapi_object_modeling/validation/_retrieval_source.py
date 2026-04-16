from __future__ import annotations

from typing import Any

from trapi_object_modeling.models.retrieval_source import RetrievalSource
from trapi_object_modeling.validation._util import (
    Location,
    SemanticValidationError,
    SemanticValidationErrorList,
    SemanticValidationResult,
    SemanticValidationWarningList,
    extend_location,
    semantic_validate,
    validate_url,
)


@semantic_validate.register(RetrievalSource)
def _validate_retrieval_source(  # pyright: ignore[reportUnusedFunction]
    obj: RetrievalSource,
    location: Location | None = None,
    **kwargs: Any,  # pyright: ignore[reportUnusedParameter]
) -> SemanticValidationResult:
    warnings, errors = (
        SemanticValidationWarningList(),
        SemanticValidationErrorList(),
    )
    if (
        obj.upstream_resource_ids is not None
        and obj.resource_id in obj.upstream_resource_ids
    ):
        errors.append(
            SemanticValidationError(
                f"resoure_id {obj.resource_id} cannot be present in upstream_resource_ids.",
                extend_location(location, "upstream_resource_ids"),
            )
        )

    if obj.source_record_urls is not None:
        for url in obj.source_record_urls:
            new_warn, new_err = validate_url(
                url, location=extend_location(location, "callback")
            )
            warnings.extend(new_warn)
            errors.extend(new_err)

    return warnings, errors
