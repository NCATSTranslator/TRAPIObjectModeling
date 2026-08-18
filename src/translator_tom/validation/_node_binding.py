from __future__ import annotations

from typing import Any

from translator_tom.models.knowledge_graph import KnowledgeGraph
from translator_tom.models.node_binding import NodeBinding
from translator_tom.validation._util import (
    Location,
    SemanticValidationResult,
    always_valid,
    extend_location,
    semantic_validate,
    validate_keys_exist,
)


@semantic_validate.register(NodeBinding)
def _validate_node_binding(
    obj: NodeBinding,
    location: Location | None = None,
    *,
    kgraph: KnowledgeGraph | None = None,
    **_: Any,
) -> SemanticValidationResult:
    if kgraph is None:
        return always_valid()
    return validate_keys_exist(
        obj.ids,
        kgraph.nodes.keys(),
        "Node",
        "knowledge_graph",
        extend_location(location, "ids"),
    )
