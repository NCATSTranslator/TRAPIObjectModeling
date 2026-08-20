from __future__ import annotations

from typing import Any

from translator_tom.v2_0.models.query import Query
from translator_tom.v2_0.validation._util import (
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
    **_: Any,
) -> SemanticValidationResult:
    return validation_pipeline(
        semantic_validate(obj.message, extend_location(location, "message")),
        validate_many(
            *obj.workflow_list,
            locations=get_list_locations(
                obj.workflow_list, extend_location(location, "workflow")
            ),
            qgraph=obj.message.query_graph,  # cross-check workflow ops against the query graph
        ),
    )
