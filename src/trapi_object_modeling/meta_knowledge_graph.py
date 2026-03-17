from __future__ import annotations

from typing import Annotated, Any, override

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from trapi_object_modeling.meta_attribute import MetaAttribute
from trapi_object_modeling.meta_qualifier import MetaQualifier
from trapi_object_modeling.shared import (
    BiolinkEntity,
    BiolinkPredicate,
    KnowledgeTypeEnum,
)
from trapi_object_modeling.utils.object_base import (
    Location,
    SemanticValidationError,
    SemanticValidationErrorList,
    SemanticValidationResult,
    SemanticValidationWarningList,
    TOMBaseObject,
)
from trapi_object_modeling.utils.semantic_validation import (
    always_valid,
    extend_location,
    get_dict_locations,
    get_list_locations,
    validate_association,
    validate_category,
    validate_many,
    validate_predicate,
    validation_pipeline,
)


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
class MetaKnowledgeGraph(TOMBaseObject):
    """Knowledge-map representation of this TRAPI web service.

    The meta knowledge graph is composed of the union of most specific categories
    and predicates for each node and edge.
    """

    nodes: dict[BiolinkEntity, MetaNode]
    """Collection of the most specific node categories provided by this TRAPI web service, indexed by Biolink class CURIEs.

    A node category is only exposed here if there is
    node for which that is the most specific category available.
    """

    edges: list[MetaEdge]
    """List of the most specific edges/predicates provided by this TRAPI web service.

    A predicate is only exposed here if there is an edge
    for which the predicate is the most specific available.
    """
