from __future__ import annotations

import itertools
from typing import Any

from translator_tom.models.auxiliary_graph import AuxiliaryGraphsDict
from translator_tom.models.knowledge_graph import KnowledgeGraph
from translator_tom.models.query_graph import PathfinderQueryGraph, QueryGraph
from translator_tom.models.result import Result
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


@semantic_validate.register(Result)
def _validate_result(  # pyright: ignore[reportUnusedFunction]
    obj: Result,
    location: Location | None = None,
    *,
    kgraph: KnowledgeGraph | None = None,
    qgraph: QueryGraph | PathfinderQueryGraph | None = None,
    aux_graphs: AuxiliaryGraphsDict | None = None,
    **_: Any,
) -> SemanticValidationResult:
    return validation_pipeline(
        (
            validate_keys_exist(
                list(obj.node_bindings.keys()),
                qgraph.nodes.keys(),
                "QNode",
                "query_graph",
                extend_location(location, "node_bindings"),
            )
            if qgraph is not None
            else always_valid()
        ),
        validate_many(
            *itertools.chain(*obj.node_bindings.values()),
            locations=list(
                itertools.chain(
                    *[
                        get_list_locations(
                            bindings,
                            location=extend_location(location, "node_bindings", qnode),
                        )
                        for qnode, bindings in obj.node_bindings.items()
                    ]
                )
            ),
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
