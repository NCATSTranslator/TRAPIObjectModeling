from __future__ import annotations

from typing import Any

from translator_tom.v2_0.models.auxiliary_graph import AuxiliaryGraphsDict
from translator_tom.v2_0.models.knowledge_graph import KnowledgeGraph
from translator_tom.v2_0.models.query_graph import QueryGraph
from translator_tom.v2_0.models.result import Result
from translator_tom.v2_0.validation._util import (
    Location,
    SemanticValidationResult,
    always_valid,
    extend_location,
    get_dict_locations,
    get_list_locations,
    semantic_validate,
    validate_keys_exist,
    validate_many,
    validation_pipeline,
)


@semantic_validate.register(Result)
def _validate_result(
    obj: Result,
    location: Location | None = None,
    *,
    kgraph: KnowledgeGraph | None = None,
    qgraph: QueryGraph | None = None,
    aux_graphs: AuxiliaryGraphsDict | None = None,
    **_: Any,
) -> SemanticValidationResult:
    return validation_pipeline(
        (
            validate_keys_exist(
                obj.node_bindings.keys(),
                qgraph.nodes.keys(),
                "QNode",
                "query_graph",
                extend_location(location, "node_bindings"),
            )
            if qgraph is not None
            else always_valid()
        ),
        validate_many(
            *obj.node_bindings.values(),
            locations=get_dict_locations(
                obj.node_bindings, extend_location(location, "node_bindings")
            ),
            qgraph=qgraph,
            kgraph=kgraph,
        ),
        validate_many(
            *obj.analyses_list,
            locations=get_list_locations(
                obj.analyses_list, extend_location(location, "analyses")
            ),
            qgraph=qgraph,
            kgraph=kgraph,
            aux_graphs=aux_graphs,
        ),
    )
