from __future__ import annotations

import itertools
from typing import Any

from trapi_object_modeling.models.result import Result
from trapi_object_modeling.validation._util import (
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


@semantic_validate.register(Result)
def _validate_result(  # pyright: ignore[reportUnusedFunction]
    obj: Result, location: Location | None = None, **kwargs: Any
) -> SemanticValidationResult:
    qgraph = kwargs.get("qgraph")
    kgraph = kwargs.get("kgraph")
    aux_graphs = kwargs.get("aux_graphs")

    locations = list(
        itertools.chain(
            *[
                get_list_locations(bindings, location=extend_location(location, qnode))
                for qnode, bindings in obj.node_bindings.items()
            ]
        )
    )

    return validation_pipeline(
        (
            validate_keys_exist(
                list(obj.node_bindings.keys()),
                qgraph.nodes,
                "QNode",
                "query_graph",
                extend_location(location, "node_bindings"),
            )
            if qgraph is not None
            else always_valid()
        ),
        validate_many(
            *itertools.chain(*obj.node_bindings.values()),
            locations=locations,
            qgraph=qgraph,
            kgraph=kgraph,
        ),
        validate_many(
            *obj.analyses,
            locations=get_list_locations(
                obj.analyses, extend_location(location, "analyses")
            ),
            qgraph=qgraph,
            kgraph=kgraph,
            aux_graphs=aux_graphs,
        ),
    )
