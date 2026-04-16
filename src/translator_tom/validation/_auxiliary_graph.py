from __future__ import annotations

from typing import Any

from translator_tom.models.auxiliary_graph import AuxiliaryGraph
from translator_tom.validation._util import (
    Location,
    SemanticValidationError,
    SemanticValidationResult,
    extend_location,
    get_list_locations,
    semantic_validate,
    validate_many,
)


@semantic_validate.register(AuxiliaryGraph)
def _validate_auxiliary_graph(  # pyright: ignore[reportUnusedFunction]
    obj: AuxiliaryGraph, location: Location | None = None, **kwargs: Any
) -> SemanticValidationResult:
    kgraph = kwargs.get("kgraph")

    warnings, errors = validate_many(
        *obj.attributes,
        locations=get_list_locations(
            obj.attributes, extend_location(location, "attributes")
        ),
    )

    if kgraph is None:
        return warnings, errors

    for edge_id in obj.edges:
        if edge_id not in kgraph.edges:
            errors.append(
                SemanticValidationError(
                    f"Auxiliary references KEdge ID {edge_id} which is not present in knowledge_graph.",
                    extend_location(location, "edges"),
                )
            )

    return warnings, errors
