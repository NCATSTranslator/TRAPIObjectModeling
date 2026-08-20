from __future__ import annotations

from typing import Any

from translator_tom.v2_0.models.analysis import Analysis
from translator_tom.v2_0.models.auxiliary_graph import AuxiliaryGraphsDict
from translator_tom.v2_0.models.knowledge_graph import KnowledgeGraph
from translator_tom.v2_0.models.query_graph import QueryGraph
from translator_tom.v2_0.validation._util import (
    Location,
    SemanticValidationError,
    SemanticValidationResult,
    extend_location,
    get_dict_locations,
    get_list_locations,
    semantic_validate,
    validate_keys_exist,
    validate_many,
    validation_pipeline,
)


@semantic_validate.register(Analysis)
def _validate_analysis(
    obj: Analysis,
    location: Location | None = None,
    *,
    kgraph: KnowledgeGraph | None = None,
    qgraph: QueryGraph | None = None,
    aux_graphs: AuxiliaryGraphsDict | None = None,
    **_: Any,
) -> SemanticValidationResult:
    warnings, errors = validation_pipeline(
        validate_many(
            *obj.attributes_list,
            locations=get_list_locations(
                obj.attributes_list, extend_location(location, "attributes")
            ),
        ),
        validate_many(
            *obj.edge_bindings_dict.values(),
            locations=get_dict_locations(
                obj.edge_bindings_dict, extend_location(location, "edge_bindings")
            ),
            kgraph=kgraph,
        ),
        validate_many(
            *obj.path_bindings_dict.values(),
            locations=get_dict_locations(
                obj.path_bindings_dict, extend_location(location, "path_bindings")
            ),
            aux_graphs=aux_graphs,
        ),
    )

    # An Analysis MUST specify at least one of edge_bindings or path_bindings (anyOf).
    if not obj.edge_bindings and not obj.path_bindings:
        errors.append(
            SemanticValidationError(
                "Analysis must contain at least one of `edge_bindings` or `path_bindings`.",
                location or (),
            )
        )

    if aux_graphs is not None:
        _warnings, sg_errors = validate_keys_exist(
            obj.support_graphs_list,
            aux_graphs.keys(),
            "Support graph",
            "auxiliary_graphs",
            extend_location(location, "support_graphs"),
        )
        errors.extend(sg_errors)

    if qgraph is not None:
        _warnings, qedge_errors = validate_keys_exist(
            obj.edge_bindings_dict.keys(),
            qgraph.edges_dict.keys(),
            "QEdge",
            "query_graph",
            extend_location(location, "edge_bindings"),
        )
        errors.extend(qedge_errors)
        _warnings, qpath_errors = validate_keys_exist(
            obj.path_bindings_dict.keys(),
            qgraph.paths_dict.keys(),
            "QPath",
            "query_graph",
            extend_location(location, "path_bindings"),
        )
        errors.extend(qpath_errors)

    return warnings, errors
