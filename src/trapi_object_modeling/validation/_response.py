from __future__ import annotations

from typing import Any

from trapi_object_modeling.models.response import Response
from trapi_object_modeling.utils.config import TRAPI_CONFIG
from trapi_object_modeling.validation._util import (
    Location,
    SemanticValidationResult,
    SemanticValidationWarning,
    extend_location,
    get_list_locations,
    semantic_validate,
    validate_many,
    validation_pipeline,
)


@semantic_validate.register(Response)
def _validate_response(  # pyright: ignore[reportUnusedFunction]
    obj: Response,
    location: Location | None = None,
    **kwargs: Any,  # pyright: ignore[reportUnusedParameter]
) -> SemanticValidationResult:
    warnings, errors = validation_pipeline(
        semantic_validate(obj.message, location),
        validate_many(
            *obj.logs,
            locations=get_list_locations(obj.logs, extend_location(location, "logs")),
        ),
        validate_many(
            *obj.workflow_list,
            locations=get_list_locations(
                obj.workflow_list, extend_location(location, "workflow")
            ),
            qgraph=obj.message.query_graph,
        ),
    )
    if obj.schema_version != TRAPI_CONFIG.schema_version:
        warnings.append(
            SemanticValidationWarning(
                f"Response schema_version `{obj.schema_version}` does not match TOM schema_version `{TRAPI_CONFIG.schema_version}`.",
                extend_location(location, "schema_version"),
            ),
        )
    if obj.biolink_version != TRAPI_CONFIG.biolink_version:
        warnings.append(
            SemanticValidationWarning(
                f"Response biolink_version `{obj.biolink_version}` does not match configured TOM biolink_version `{TRAPI_CONFIG.biolink_version}`."
            )
        )

    return warnings, errors
