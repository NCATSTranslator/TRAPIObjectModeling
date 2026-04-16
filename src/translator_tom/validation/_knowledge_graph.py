"""Validators for KnowledgeGraph, Node, and Edge."""

from __future__ import annotations

from typing import Any

from translator_tom.models.knowledge_graph import Edge, KnowledgeGraph, Node
from translator_tom.models.retrieval_source import ResourceRoleEnum
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
    validate_predicate,
    validation_pipeline,
)


@semantic_validate.register(KnowledgeGraph)
def _validate_knowledge_graph(  # pyright: ignore[reportUnusedFunction]
    obj: KnowledgeGraph,
    location: Location | None = None,
    **kwargs: Any,  # pyright: ignore[reportUnusedParameter]
) -> SemanticValidationResult:
    return validation_pipeline(
        validate_many(
            *obj.nodes.values(),
            locations=get_dict_locations(obj.nodes, extend_location(location, "nodes")),
        ),
        validate_many(
            *obj.edges.values(),
            locations=get_dict_locations(obj.edges, extend_location(location, "edges")),
            kgraph=obj,
        ),
    )


@semantic_validate.register(Node)
def _validate_node(  # pyright: ignore[reportUnusedFunction]
    obj: Node,
    location: Location | None = None,
    **kwargs: Any,  # pyright: ignore[reportUnusedParameter]
) -> SemanticValidationResult:
    return validation_pipeline(
        *(
            validate_category(category, extend_location(location, "categories"))
            for category in obj.categories
        ),
        validate_many(
            *obj.attributes,
            locations=get_list_locations(
                obj.attributes, extend_location(location, "attributes")
            ),
        ),
    )


@semantic_validate.register(Edge)
def _validate_edge(  # pyright: ignore[reportUnusedFunction]
    obj: Edge, location: Location | None = None, **kwargs: Any
) -> SemanticValidationResult:
    kgraph: KnowledgeGraph | None = kwargs.get("kgraph")

    warnings, errors = validation_pipeline(
        validate_predicate(obj.predicate, extend_location(location, "predicate")),
        validate_many(
            *obj.qualifiers_list,
            locations=get_list_locations(
                obj.qualifiers_list, extend_location(location, "qualifiers")
            ),
        ),
        validate_many(
            *obj.sources,
            locations=get_list_locations(
                obj.sources, extend_location(location, "sources")
            ),
        ),
        validate_many(
            *obj.attributes_list,
            locations=get_list_locations(
                obj.attributes_list, extend_location(location, "attributes")
            ),
        ),
    )

    if kgraph is not None:
        if obj.subject not in kgraph.nodes:
            errors.append(
                SemanticValidationError(
                    f"Subject `{obj.subject}` is not present in knowledge_graph.",
                    extend_location(location, "subject"),
                )
            )
        if obj.object not in kgraph.nodes:
            errors.append(
                SemanticValidationError(
                    f"Object `{obj.object}` is not present in knowledge_graph.",
                    extend_location(location, "object"),
                )
            )

    has_primary = any(
        source.resource_role == ResourceRoleEnum.primary_knowledge_source
        for source in obj.sources
    )
    if not has_primary:
        errors.append(
            SemanticValidationError(
                "Edge is missing primary_knowledge_source.",
                extend_location(location, "sources"),
            )
        )

    return warnings, errors
