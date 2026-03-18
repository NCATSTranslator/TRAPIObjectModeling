from __future__ import annotations

from typing import Annotated, Any, override

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from trapi_object_modeling.attribute import Attribute
from trapi_object_modeling.knowledge_graph import KnowledgeGraph
from trapi_object_modeling.shared import AuxGraphID, EdgeID
from trapi_object_modeling.utils.object_base import (
    Location,
    SemanticValidationError,
    SemanticValidationResult,
    TOMBaseObject,
)
from trapi_object_modeling.utils.semantic_validation import (
    extend_location,
    get_list_locations,
    validate_many,
)


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
class AuxiliaryGraph(TOMBaseObject):
    """A single AuxiliaryGraph instance that is used by Knowledge Graph Edges, Result Analysis support graphs, and Path Bindings.

    Edges comprising an Auxiliary Graph are a subset of the
    Knowledge Graph in the message. Data creators can
    create an AuxiliaryGraph to assemble a specific collection
    of edges from the Knowledge Graph into a named graph that can be
    referenced from an Edge as evidence/explanation supporting that Edge,
    from a Result Analysis as information used to generate a score, or
    from a Path Binding as the path for that Analysis.
    """

    edges: Annotated[list[EdgeID], Field(min_length=1)]
    """List of edges that form the Auxiliary Graph.

    Each item is a reference to a single Knowledge Graph Edge. This list is not
    ordered, nor is the order intended to convey any relationship
    between the edges that form this Auxiliary Graph.
    """

    attributes: list[Attribute]
    """Attributes of the Auxiliary Graph."""

    @override
    def semantic_validate(
        self,
        location: Location | None = None,
        kgraph: KnowledgeGraph | None = None,
        **kwargs: Any,
    ) -> SemanticValidationResult:
        warnings, errors = validate_many(
            *self.attributes,
            locations=get_list_locations(
                self.attributes, extend_location(location, "attributes")
            ),
        )

        if kgraph is None:
            return warnings, errors

        for edge_id in self.edges:
            if edge_id not in kgraph.edges:
                errors.append(
                    SemanticValidationError(
                        f"Auxiliary references KEdge ID {edge_id} which is not present in knowledge_graph.",
                        extend_location(location, "edges"),
                    )
                )

        return warnings, errors


AuxiliaryGraphsDict = dict[AuxGraphID, AuxiliaryGraph]
