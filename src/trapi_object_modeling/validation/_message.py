"""Validator for Message."""

from __future__ import annotations

from typing import Any

from trapi_object_modeling.message import Message
from trapi_object_modeling.validation._util import (
    Location,
    SemanticValidationResult,
    always_valid,
    extend_location,
    get_dict_locations,
    get_list_locations,
    semantic_validate,
    valid_if_missing,
    validate_many,
    validation_pipeline,
)


@semantic_validate.register(Message)
def _validate_message(  # pyright: ignore[reportUnusedFunction]
    obj: Message,
    location: Location | None = None,
    **kwargs: Any,  # pyright:ignore[reportUnusedParameter]
) -> SemanticValidationResult:
    return validation_pipeline(
        valid_if_missing(
            obj.knowledge_graph, extend_location(location, "knowledge_graph")
        ),
        valid_if_missing(obj.query_graph, extend_location(location, "query_graph")),
        (
            validate_many(
                *obj.auxiliary_graphs.values(),
                locations=get_dict_locations(
                    obj.auxiliary_graphs,
                    extend_location(location, "auxiliary_graphs"),
                ),
                kgraph=obj.knowledge_graph,
            )
            if obj.auxiliary_graphs is not None
            else always_valid()
        ),
        validate_many(
            *obj.results_list,
            locations=get_list_locations(
                obj.results_list, extend_location(location, "results")
            ),
            qgraph=obj.query_graph,
            kgraph=obj.knowledge_graph,
            aux_graphs=obj.auxiliary_graphs,
        ),
    )
