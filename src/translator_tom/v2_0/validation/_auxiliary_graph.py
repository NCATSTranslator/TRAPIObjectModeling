from __future__ import annotations

from typing import Any

from translator_tom.v2_0.models.auxiliary_graph import AuxiliaryGraph
from translator_tom.v2_0.models.knowledge_graph import KnowledgeGraph
from translator_tom.v2_0.validation._util import (
    Location,
    SemanticValidationResult,
    always_valid,
    extend_location,
    semantic_validate,
    validate_keys_exist,
)


@semantic_validate.register(AuxiliaryGraph)
def _validate_auxiliary_graph(
    obj: AuxiliaryGraph,
    location: Location | None = None,
    *,
    kgraph: KnowledgeGraph | None = None,
    **_: Any,
) -> SemanticValidationResult:
    if kgraph is None:
        return always_valid()
    return validate_keys_exist(
        obj.edges,
        kgraph.edges_dict.keys(),
        "KEdge",
        "knowledge_graph",
        extend_location(location, "edges"),
    )
