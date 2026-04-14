from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from trapi_object_modeling.attribute import Attribute
from trapi_object_modeling.shared import CURIE

if TYPE_CHECKING:
    from trapi_object_modeling.knowledge_graph import KnowledgeGraph
    from trapi_object_modeling.query_graph import PathfinderQueryGraph, QueryGraph
from trapi_object_modeling.utils.object_base import (
    Location,
    SemanticValidationResult,
    TOMBaseObject,
)
from trapi_object_modeling.utils.semantic_validation import (
    always_valid,
    extend_location,
    get_list_locations,
    validate_many,
    validation_pipeline,
)


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
class NodeBinding(TOMBaseObject):
    """An instance of NodeBinding is a single KnowledgeGraph Node mapping, identified by the corresponding 'id' object key identifier of the Node within the Knowledge Graph.

    Instances of NodeBinding may include extra annotation in the form of additional properties
    (such annotation is not yet fully standardized).
    Each Node Binding must bind directly to node in the original Query Graph.
    """

    id: CURIE
    """The CURIE of a Node within the Knowledge Graph."""

    query_id: CURIE | None = None
    """An optional property to provide the CURIE in the QueryGraph to which this binding applies.

    If the bound QNode does not have an
    an 'id' property or if it is empty, then this query_id MUST be
    null or absent. If the bound QNode has one or more CURIEs
    as an 'id' and this NodeBinding's 'id' refers to a QNode 'id'
    in a manner where the CURIEs are different (typically due to
    the NodeBinding.id being a descendant of a QNode.id), then
    this query_id MUST be provided. In other cases, there is no
    ambiguity, and this query_id SHOULD NOT be provided.
    """

    attributes: list[Attribute]
    """A list of attributes providing further information about the node binding.
    This is not intended for capturing node attributes
    and should only be used for properties that vary from result to
    result.
    """

    @override
    def semantic_validate(
        self,
        location: Location | None = None,
        qgraph: QueryGraph | PathfinderQueryGraph | None = None,
        kgraph: KnowledgeGraph | None = None,
        **kwargs: Any,
    ) -> SemanticValidationResult:
        return validation_pipeline(
            (
                kgraph.validate_nodes_exist([self.id], extend_location(location, "id"))
                if kgraph is not None
                else always_valid()
            ),
            (
                qgraph.validate_qnodes_exist(
                    [self.query_id], extend_location(location, "query_id")
                )
                if qgraph is not None and self.query_id is not None
                else always_valid()
            ),
            validate_many(
                *self.attributes,
                locations=get_list_locations(
                    self.attributes, extend_location(location, "attributes")
                ),
            ),
        )
