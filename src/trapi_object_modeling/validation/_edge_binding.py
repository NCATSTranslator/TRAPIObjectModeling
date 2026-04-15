from __future__ import annotations

from typing import Any

from trapi_object_modeling.edge_binding import EdgeBinding
from trapi_object_modeling.validation._util import (
    Location,
    SemanticValidationResult,
    always_valid,
    extend_location,
    get_list_locations,
    semantic_validate,
    validate_many,
    validation_pipeline,
)


@semantic_validate.register(EdgeBinding)
def _validate_edge_binding(  # pyright: ignore[reportUnusedFunction]
    obj: EdgeBinding, location: Location | None = None, **kwargs: Any
) -> SemanticValidationResult:
    kgraph = kwargs.get("kgraph")

    return validation_pipeline(
        (
            kgraph.validate_edges_exist([obj.id], extend_location(location, "id"))
            if kgraph is not None
            else always_valid()
        ),
        validate_many(
            *obj.attributes,
            locations=get_list_locations(
                obj.attributes, extend_location(location, "attributes")
            ),
        ),
    )
