"""Validators for MetaKnowledgeGraph, MetaNode, and MetaEdge."""

from __future__ import annotations

from typing import Any

from translator_tom.models.meta_knowledge_graph import (
    MetaEdge,
    MetaKnowledgeGraph,
    MetaNode,
)
from translator_tom.validation._util import (
    Location,
    SemanticValidationResult,
    always_valid,
    extend_location,
    get_dict_locations,
    get_list_locations,
    semantic_validate,
    validate_association,
    validate_category,
    validate_keys_exist,
    validate_many,
    validate_predicate,
    validation_pipeline,
)


@semantic_validate.register(MetaKnowledgeGraph)
def _validate_meta_knowledge_graph(  # pyright: ignore[reportUnusedFunction]
    obj: MetaKnowledgeGraph,
    location: Location | None = None,
    **kwargs: Any,  # pyright: ignore[reportUnusedParameter]
) -> SemanticValidationResult:
    return validation_pipeline(
        *(
            validate_category(cat, extend_location(location, "nodes"))
            for cat in obj.nodes
        ),
        validate_many(
            *obj.nodes.values(),
            locations=get_dict_locations(obj.nodes, extend_location(location, "nodes")),
        ),
        validate_many(
            *obj.edges,
            locations=get_list_locations(obj.edges, extend_location(location, "edges")),
            metakg=obj,
        ),
    )


@semantic_validate.register(MetaNode)
def _validate_meta_node(  # pyright: ignore[reportUnusedFunction]
    obj: MetaNode,
    location: Location | None = None,
    **kwargs: Any,  # pyright: ignore[reportUnusedParameter]
) -> SemanticValidationResult:
    return validate_many(
        *obj.attributes_list,
        locations=get_list_locations(
            obj.attributes_list, extend_location(location, "attributes")
        ),
    )


@semantic_validate.register(MetaEdge)
def _validate_meta_edge(  # pyright: ignore[reportUnusedFunction]
    obj: MetaEdge, location: Location | None = None, **kwargs: Any
) -> SemanticValidationResult:
    metakg: MetaKnowledgeGraph | None = kwargs.get("metakg")

    return validation_pipeline(
        validate_category(obj.subject, extend_location(location, "subject")),
        (
            validate_keys_exist(
                [obj.subject],
                metakg.nodes,
                "Node",
                "meta_knowledge_graph",
                extend_location(location, "subject"),
            )
            if metakg is not None
            else always_valid()
        ),
        (
            validate_keys_exist(
                [obj.object],
                metakg.nodes,
                "Node",
                "meta_knowledge_graph",
                extend_location(location, "object"),
            )
            if metakg is not None
            else always_valid()
        ),
        validate_category(obj.object, extend_location(location, "object")),
        validate_predicate(obj.predicate, extend_location(location, "predicate")),
        validate_many(
            *obj.attributes_list,
            locations=get_list_locations(
                obj.attributes_list, extend_location(location, "attributes")
            ),
        ),
        validate_many(
            *obj.qualifiers_list,
            locations=get_list_locations(
                obj.qualifiers_list, extend_location(location, "qualifiers")
            ),
        ),
        validate_association(obj.association, extend_location(location, "association"))
        if obj.association is not None
        else always_valid(),
    )
