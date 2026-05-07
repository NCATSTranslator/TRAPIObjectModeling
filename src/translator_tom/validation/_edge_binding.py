from __future__ import annotations

from typing import Any

from translator_tom.models.edge_binding import EdgeBinding
from translator_tom.models.knowledge_graph import KnowledgeGraph
from translator_tom.validation._util import (
    Location,
    SemanticValidationResult,
    always_valid,
    extend_location,
    get_list_locations,
    semantic_validate,
    validate_keys_exist,
    validate_many,
    validation_pipeline,
)


@semantic_validate.register(EdgeBinding)
def _validate_edge_binding(
    obj: EdgeBinding,
    location: Location | None = None,
    *,
    kgraph: KnowledgeGraph | None = None,
    **_: Any,
) -> SemanticValidationResult:
    return validation_pipeline(
        (
            validate_keys_exist(
                [obj.id],
                kgraph.edges.keys(),
                "Edge",
                "knowledge_graph",
                extend_location(location, "id"),
            )
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
