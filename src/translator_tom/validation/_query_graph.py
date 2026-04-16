from __future__ import annotations

from typing import Any

from translator_tom.models.query_graph import (
    PathfinderQueryGraph,
    QEdge,
    QNode,
    QPath,
    QueryGraph,
)
from translator_tom.validation._util import (
    Location,
    SemanticValidationError,
    SemanticValidationResult,
    extend_location,
    get_dict_locations,
    get_list_locations,
    semantic_validate,
    validate_category,
    validate_many,
    validate_node_exists,
    validate_predicate,
    validation_pipeline,
)


def _validate_base_query_graph(
    obj: QueryGraph | PathfinderQueryGraph,
    location: Location | None,
    **kwargs: Any,  # pyright: ignore[reportUnusedParameter]
) -> SemanticValidationResult:
    """Shared validation for all query graph types (node validation)."""
    return validate_many(
        *obj.nodes.values(),
        locations=get_dict_locations(obj.nodes, extend_location(location, "nodes")),
    )


@semantic_validate.register(QueryGraph)
def _validate_query_graph(  # pyright: ignore[reportUnusedFunction]
    obj: QueryGraph, location: Location | None = None, **kwargs: Any
) -> SemanticValidationResult:
    return validation_pipeline(
        _validate_base_query_graph(obj, location, **kwargs),
        validate_many(
            *obj.edges.values(),
            locations=get_dict_locations(obj.edges, extend_location(location, "edges")),
            qgraph=obj,
        ),
    )


@semantic_validate.register(PathfinderQueryGraph)
def _validate_pathfinder_query_graph(  # pyright: ignore[reportUnusedFunction]
    obj: PathfinderQueryGraph, location: Location | None = None, **kwargs: Any
) -> SemanticValidationResult:
    return validation_pipeline(
        _validate_base_query_graph(obj, location, **kwargs),
        validate_many(
            *obj.paths.values(),
            locations=get_dict_locations(obj.paths, extend_location(location, "paths")),
            qgraph=obj,
        ),
    )


@semantic_validate.register(QNode)
def _validate_qnode(  # pyright: ignore[reportUnusedFunction]
    obj: QNode,
    location: Location | None = None,
    **kwargs: Any,  # pyright: ignore[reportUnusedParameter]
) -> SemanticValidationResult:
    return validation_pipeline(
        *(
            validate_category(cat, extend_location(location, "categories"))
            for cat in obj.categories_list
        ),
        validate_many(
            *obj.constraints_list,
            locations=get_list_locations(
                obj.constraints_list, extend_location(location, "constraints")
            ),
        ),
    )


@semantic_validate.register(QEdge)
def _validate_qedge(  # pyright: ignore[reportUnusedFunction]
    obj: QEdge, location: Location | None = None, **kwargs: Any
) -> SemanticValidationResult:
    qgraph: QueryGraph | PathfinderQueryGraph | None = kwargs.get("qgraph")

    warnings, errors = validation_pipeline(
        *(
            validate_predicate(predicate, extend_location(location, "predicates"))
            for predicate in obj.predicates_list
        ),
        validate_many(
            *obj.qualifier_constraints_list,
            locations=get_list_locations(
                obj.qualifier_constraints_list,
                extend_location(location, "qualifier_constraints"),
            ),
        ),
        validate_many(
            *obj.attribute_constraints_list,
            locations=get_list_locations(
                obj.attribute_constraints_list,
                extend_location(location, "attribute_constraints"),
            ),
        ),
    )

    if qgraph is not None:
        w, e = validate_node_exists(
            obj, "subject", qgraph, "query_graph", extend_location(location, "subject")
        )
        warnings.extend(w)
        errors.extend(e)
        w, e = validate_node_exists(
            obj, "object", qgraph, "query_graph", extend_location(location, "object")
        )
        warnings.extend(w)
        errors.extend(e)

    if qgraph is not None and isinstance(qgraph, QueryGraph):
        if obj.subject not in qgraph.nodes:
            errors.append(
                SemanticValidationError(
                    f"Subject `{obj.subject}` is not present in query_graph.",
                    extend_location(location, "subject"),
                )
            )
        if obj.object not in qgraph.nodes:
            errors.append(
                SemanticValidationError(
                    f"Object `{obj.object}` is not present in query_graph.",
                    extend_location(location, "object"),
                )
            )

    return warnings, errors


@semantic_validate.register(QPath)
def _validate_qpath(  # pyright: ignore[reportUnusedFunction]
    obj: QPath, location: Location | None = None, **kwargs: Any
) -> SemanticValidationResult:
    qgraph: QueryGraph | PathfinderQueryGraph | None = kwargs.get("qgraph")

    warnings, errors = validation_pipeline(
        *(
            validate_predicate(predicate, extend_location(location, "predicates"))
            for predicate in obj.predicates_list
        ),
        validate_many(
            *obj.constraints_list,
            locations=get_list_locations(
                obj.constraints_list, extend_location(location, "constraints")
            ),
        ),
    )

    if qgraph is not None:
        w, e = validate_node_exists(
            obj, "subject", qgraph, "query_graph", extend_location(location, "subject")
        )
        warnings.extend(w)
        errors.extend(e)
        w, e = validate_node_exists(
            obj, "object", qgraph, "query_graph", extend_location(location, "object")
        )
        warnings.extend(w)
        errors.extend(e)

    return warnings, errors
