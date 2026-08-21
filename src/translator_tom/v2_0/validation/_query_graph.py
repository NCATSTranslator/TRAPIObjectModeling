from __future__ import annotations

from typing import Any

from translator_tom.utils.shared import Curie
from translator_tom.v2_0.models.constraints import QEdgeConstraints
from translator_tom.v2_0.models.query_graph import (
    QEdge,
    QNode,
    QPath,
    QueryGraph,
)
from translator_tom.v2_0.validation._util import (
    Location,
    SemanticValidationError,
    SemanticValidationResult,
    always_valid,
    extend_location,
    get_dict_locations,
    get_list_locations,
    semantic_validate,
    validate_category,
    validate_many,
    validate_node_exists,
    validate_permissible_value,
    validate_predicate,
    validation_pipeline,
)


@semantic_validate.register(QueryGraph)
def _validate_query_graph(
    obj: QueryGraph,
    location: Location | None = None,
    **_: Any,
) -> SemanticValidationResult:
    return validation_pipeline(
        validate_many(
            *obj.nodes.values(),
            locations=get_dict_locations(obj.nodes, extend_location(location, "nodes")),
        ),
        validate_many(
            *obj.edges_dict.values(),
            locations=get_dict_locations(
                obj.edges_dict, extend_location(location, "edges")
            ),
            qgraph=obj,
        ),
        validate_many(
            *obj.paths_dict.values(),
            locations=get_dict_locations(
                obj.paths_dict, extend_location(location, "paths")
            ),
            qgraph=obj,
        ),
    )


@semantic_validate.register(QNode)
def _validate_qnode(
    obj: QNode,
    location: Location | None = None,
    **_: Any,
) -> SemanticValidationResult:
    return validation_pipeline(
        validate_many(
            *obj.constraints_list,
            locations=get_list_locations(
                obj.constraints_list, extend_location(location, "constraints")
            ),
        ),
        *(
            validate_category(cat, extend_location(location, "categories"))
            for cat in obj.categories_list
        ),
    )


def _validate_qedge_constraints(
    constraints: QEdgeConstraints,
    location: Location | None = None,
) -> SemanticValidationResult:
    """Validate the values within a QEdge's constraints.

    A QEdgeConstraints object MUST hold at least one constraint (`minProperties: 1`;
    not enforced at parse time for performance). knowledge_level/agent_type values
    MUST be valid biolink enum values, source values MUST be infores CURIEs, and
    qualifier-set constraint keys MUST be biolink CURIEs (`patternProperties ^biolink:`,
    likewise skipped at parse time). Attribute constraints are validated individually.
    """
    warnings, errors = validate_many(
        *constraints.attributes_list,
        locations=get_list_locations(
            constraints.attributes_list, extend_location(location, "attributes")
        ),
    )

    has_constraint = bool(constraints.extra_dict) or any(
        value is not None
        for value in (
            constraints.knowledge_level,
            constraints.agent_type,
            constraints.attributes,
            constraints.qualifiers,
            constraints.sources,
        )
    )
    if not has_constraint:
        errors.append(
            SemanticValidationError(
                "QEdge `constraints` must contain at least one constraint.",
                location or (),
            )
        )

    for i, qualifier_set in enumerate(constraints.qualifiers_list):
        for qualifier_type_id in qualifier_set:
            if Curie.get_prefix(qualifier_type_id) != "biolink":
                errors.append(
                    SemanticValidationError(
                        f"Qualifier constraint type `{qualifier_type_id}` is not a biolink CURIE.",
                        extend_location(location, "qualifiers", i),
                    )
                )

    if constraints.knowledge_level is not None:
        for i, value in enumerate(constraints.knowledge_level.values):
            _, new_errors = validate_permissible_value(
                value,
                "KnowledgeLevelEnum",
                extend_location(location, "knowledge_level", "values", i),
            )
            errors.extend(new_errors)

    if constraints.agent_type is not None:
        for i, value in enumerate(constraints.agent_type.values):
            _, new_errors = validate_permissible_value(
                value,
                "AgentTypeEnum",
                extend_location(location, "agent_type", "values", i),
            )
            errors.extend(new_errors)

    if constraints.sources is not None:
        for i, value in enumerate(constraints.sources.values):
            if Curie.get_prefix(value) != "infores":
                errors.append(
                    SemanticValidationError(
                        f"Source constraint value `{value}` is not an infores CURIE.",
                        extend_location(location, "sources", "values", i),
                    )
                )

    return warnings, errors


@semantic_validate.register(QEdge)
def _validate_qedge(
    obj: QEdge,
    location: Location | None = None,
    *,
    qgraph: QueryGraph | None = None,
    **_: Any,
) -> SemanticValidationResult:
    warnings, errors = always_valid()

    for predicate in obj.predicates_list:
        new_warnings, new_errors = validate_predicate(
            predicate, extend_location(location, "predicates")
        )
        warnings.extend(new_warnings)
        errors.extend(new_errors)

    if obj.constraints is not None:
        new_warnings, new_errors = _validate_qedge_constraints(
            obj.constraints, extend_location(location, "constraints")
        )
        warnings.extend(new_warnings)
        errors.extend(new_errors)

    if qgraph is not None:
        new_warnings, new_errors = validate_node_exists(
            obj, "subject", qgraph, "query_graph", extend_location(location, "subject")
        )
        warnings.extend(new_warnings)
        errors.extend(new_errors)
        new_warnings, new_errors = validate_node_exists(
            obj, "object", qgraph, "query_graph", extend_location(location, "object")
        )
        warnings.extend(new_warnings)
        errors.extend(new_errors)

    return warnings, errors


@semantic_validate.register(QPath)
def _validate_qpath(
    obj: QPath,
    location: Location | None = None,
    *,
    qgraph: QueryGraph | None = None,
    **_: Any,
) -> SemanticValidationResult:
    warnings, errors = validation_pipeline(
        validate_many(
            *obj.constraints_list,
            locations=get_list_locations(
                obj.constraints_list, extend_location(location, "constraints")
            ),
        ),
        *(
            validate_predicate(predicate, extend_location(location, "predicates"))
            for predicate in obj.predicates_list
        ),
    )

    if qgraph is not None:
        new_warnings, new_errors = validate_node_exists(
            obj, "subject", qgraph, "query_graph", extend_location(location, "subject")
        )
        warnings.extend(new_warnings)
        errors.extend(new_errors)
        new_warnings, new_errors = validate_node_exists(
            obj, "object", qgraph, "query_graph", extend_location(location, "object")
        )
        warnings.extend(new_warnings)
        errors.extend(new_errors)

    return warnings, errors
