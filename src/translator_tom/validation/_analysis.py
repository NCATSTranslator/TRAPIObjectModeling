"""Validators for Analysis and PathfinderAnalysis."""

from __future__ import annotations

import itertools
from typing import Any

from translator_tom.models.analysis import (
    Analysis,
    BaseAnalysis,
    PathfinderAnalysis,
)
from translator_tom.models.query_graph import QueryGraph
from translator_tom.validation._util import (
    Location,
    SemanticValidationError,
    SemanticValidationResult,
    extend_location,
    get_list_locations,
    semantic_validate,
    validate_many,
    validation_pipeline,
)


def _validate_base_analysis(
    obj: BaseAnalysis, location: Location | None, **kwargs: Any
) -> SemanticValidationResult:
    """Shared validation for all analysis types."""
    aux_graphs = kwargs.get("aux_graphs")

    warnings, errors = validate_many(
        *obj.attributes_list,
        locations=get_list_locations(
            obj.attributes_list, location=extend_location(location, "attributes")
        ),
    )

    if aux_graphs is None:
        return warnings, errors

    for i, aux_id in enumerate(obj.support_graphs_list):
        if aux_id not in aux_graphs:
            errors.append(
                SemanticValidationError(
                    f"Support graph {aux_id} not present in auxiliary_graphs.",
                    (*(location or ()), "support_graphs", i),
                )
            )

    return warnings, errors


@semantic_validate.register(Analysis)
def _validate_analysis(  # pyright:ignore[reportUnusedFunction]
    obj: Analysis, location: Location | None = None, **kwargs: Any
) -> SemanticValidationResult:
    qgraph = kwargs.get("qgraph")
    kgraph = kwargs.get("kgraph")

    locations = list(
        itertools.chain(
            *[
                get_list_locations(bindings, location=extend_location(location, qedge))
                for qedge, bindings in obj.edge_bindings.items()
            ]
        )
    )

    warnings, errors = validation_pipeline(
        _validate_base_analysis(obj, location, **kwargs),
        validate_many(
            *itertools.chain(*obj.edge_bindings.values()),
            locations=locations,
            kgraph=kgraph,
        ),
    )

    if qgraph is None or not isinstance(qgraph, QueryGraph):
        return warnings, errors

    for qedge_id in obj.edge_bindings:
        if qedge_id not in qgraph.edges:
            errors.append(
                SemanticValidationError(
                    f"QEdge {qedge_id} is not present in query_graph.",
                    (*(location or ()), "edge_binding", qedge_id),
                )
            )

    return warnings, errors


@semantic_validate.register(PathfinderAnalysis)
def _validate_pathfinder_analysis(  # pyright:ignore[reportUnusedFunction]
    obj: PathfinderAnalysis, location: Location | None = None, **kwargs: Any
) -> SemanticValidationResult:
    qgraph = kwargs.get("qgraph")
    kgraph = kwargs.get("kgraph")

    locations = list(
        itertools.chain(
            *[
                get_list_locations(bindings, location=extend_location(location, qpath))
                for qpath, bindings in obj.path_bindings.items()
            ]
        )
    )

    warnings, errors = validation_pipeline(
        _validate_base_analysis(obj, location, **kwargs),
        validate_many(
            *itertools.chain(*obj.path_bindings.values()),
            locations=locations,
            kgraph=kgraph,
        ),
    )

    if qgraph is None:
        return warnings, errors

    for qpath_id in obj.path_bindings:
        if qpath_id not in qgraph.paths:
            errors.append(
                SemanticValidationError(
                    f"QPath {qpath_id} is not present in query_graph.",
                    (*(location or ()), "path_bindings", qpath_id),
                )
            )

    return warnings, errors
