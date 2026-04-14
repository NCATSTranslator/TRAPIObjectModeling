from __future__ import annotations

import itertools
from typing import TYPE_CHECKING, Annotated, Any, override

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from trapi_object_modeling.analysis import Analysis, PathfinderAnalysis
from trapi_object_modeling.node_binding import NodeBinding
from trapi_object_modeling.shared import EdgeID, QNodeID

if TYPE_CHECKING:
    from trapi_object_modeling.auxiliary_graph import AuxiliaryGraphsDict
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
class Result(TOMBaseObject):
    """A Result object specifies the nodes and edges in the knowledge graph that satisfy the structure or conditions of a user-submitted query graph.

    It must contain a NodeBindings object (list of query graph node
    to knowledge graph node mappings) and a list of Analysis objects.
    """

    node_bindings: Annotated[
        dict[QNodeID, Annotated[list[NodeBinding], Field(min_length=1)]],
        Field(min_length=1),
    ]
    """The dictionary of Input Query Graph to Result Knowledge Graph node bindings where the dictionary keys are the key identifiers of the Query Graph nodes and the associated values of those keys are instances of NodeBinding schema type (see below).

    This value is an array of NodeBindings since a given query node may have multiple
    knowledge graph Node bindings in the result.
    """

    analyses: list[Analysis | PathfinderAnalysis]
    """The list of all Analysis components that contribute to the result."""

    @override
    def semantic_validate(
        self,
        location: Location | None = None,
        qgraph: QueryGraph | PathfinderQueryGraph | None = None,
        kgraph: KnowledgeGraph | None = None,
        aux_graphs: AuxiliaryGraphsDict | None = None,
        **kwargs: Any,
    ) -> SemanticValidationResult:
        locations = list(
            itertools.chain(
                *[
                    get_list_locations(
                        bindings, location=extend_location(location, qnode)
                    )
                    for qnode, bindings in self.node_bindings.items()
                ]
            )
        )

        return validation_pipeline(
            (
                qgraph.validate_qnodes_exist(
                    list(self.node_bindings.keys()),
                    extend_location(location, "node_bindings"),
                )
                if qgraph is not None
                else always_valid()
            ),
            validate_many(
                *itertools.chain(*self.node_bindings.values()),
                locations=locations,
                qgraph=qgraph,
                kgraph=kgraph,
            ),
            validate_many(
                *self.analyses,
                locations=get_list_locations(
                    self.analyses, extend_location(location, "analyses")
                ),
                qgraph=qgraph,
                kgraph=kgraph,
                aux_graphs=aux_graphs,
            ),
        )

    def normalize(self, mapping: dict[EdgeID, EdgeID]) -> None:
        """Normalize the result given a mapping of old:new EdgeIDs."""
        for analysis in self.analyses:
            if not isinstance(analysis, Analysis):
                continue
            for binding in itertools.chain(
                *(bindings for bindings in analysis.edge_bindings.values())
            ):
                binding.id = mapping.get(binding.id, binding.id)
