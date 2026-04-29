from __future__ import annotations

import itertools
from typing import Any

from translator_tom.models.knowledge_graph import KnowledgeGraph
from translator_tom.models.node_binding import NodeBinding
from translator_tom.models.query_graph import PathfinderQueryGraph, QueryGraph
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


@semantic_validate.register(NodeBinding)
def _validate_node_binding(  # pyright: ignore[reportUnusedFunction]
    obj: NodeBinding,
    location: Location | None = None,
    *,
    kgraph: KnowledgeGraph | None = None,
    qgraph: QueryGraph | PathfinderQueryGraph | None = None,
    **_: Any,
) -> SemanticValidationResult:
    return validation_pipeline(
        (
            validate_keys_exist(
                [obj.id],
                kgraph.nodes.keys(),
                "Node",
                "knowledge_graph",
                extend_location(location, "id"),
            )
            if kgraph is not None
            else always_valid()
        ),
        (
            validate_keys_exist(
                [obj.query_id],
                list(
                    itertools.chain(*(node.ids_list for node in qgraph.nodes.values()))
                ),
                "query_id",
                "query_graph",
                extend_location(location, "query_id"),
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
