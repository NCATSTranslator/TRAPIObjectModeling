from __future__ import annotations

from typing import Any, override

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from trapi_object_modeling.attribute import Attribute
from trapi_object_modeling.knowledge_graph import KnowledgeGraph
from trapi_object_modeling.shared import EdgeID
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
class EdgeBinding(TOMBaseObject):
    """A instance of EdgeBinding is a single KnowledgeGraph Edge mapping, identified by the corresponding 'id' object key identifier of the Edge within the Knowledge Graph.

    Instances of EdgeBinding may include extra annotation
    (such annotation is not yet fully standardized).
    Edge bindings are captured within a specific reasoner's Analysis
    object because the Edges in the Knowledge Graph that get bound to
    the input Query Graph may differ between reasoners.
    """

    id: EdgeID
    """The key identifier of a specific KnowledgeGraph Edge."""

    attributes: list[Attribute]
    """A list of attributes providing further information about the edge binding.
    This is not intended for capturing edge attributes
    and should only be used for properties that vary from result to
    result.
    """

    @override
    def semantic_validate(
        self,
        location: Location | None = None,
        kgraph: KnowledgeGraph | None = None,
        **kwargs: Any,
    ) -> SemanticValidationResult:
        return validation_pipeline(
            (
                kgraph.validate_edges_exist([self.id], extend_location(location, "id"))
                if kgraph is not None
                else always_valid()
            ),
            validate_many(
                *self.attributes,
                locations=get_list_locations(
                    self.attributes, extend_location(location, "attributes")
                ),
            ),
        )
