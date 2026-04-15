from __future__ import annotations

from typing import Any

from trapi_object_modeling.node_binding import NodeBinding
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


@semantic_validate.register(NodeBinding)
def _validate_node_binding(  # pyright: ignore[reportUnusedFunction]
    obj: NodeBinding, location: Location | None = None, **kwargs: Any
) -> SemanticValidationResult:
    qgraph = kwargs.get("qgraph")
    kgraph = kwargs.get("kgraph")

    return validation_pipeline(
        (
            kgraph.validate_nodes_exist([obj.id], extend_location(location, "id"))
            if kgraph is not None
            else always_valid()
        ),
        (
            qgraph.validate_qnodes_exist(
                [obj.query_id], extend_location(location, "query_id")
            )
            if qgraph is not None and obj.query_id is not None
            else always_valid()
        ),
        validate_many(
            *obj.attributes,
            locations=get_list_locations(
                obj.attributes, extend_location(location, "attributes")
            ),
        ),
    )
