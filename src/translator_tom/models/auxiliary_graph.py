from __future__ import annotations

from typing import Annotated, ClassVar, override

from pydantic import ConfigDict, Field

from translator_tom.models.attribute import Attribute
from translator_tom.models.shared import AuxGraphID, EdgeID
from translator_tom.utils.hash import tomhash
from translator_tom.utils.object_base import TOMBaseObject


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

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")

    edges: Annotated[list[EdgeID], Field(min_length=1)]
    """List of edges that form the Auxiliary Graph.

    Each item is a reference to a single Knowledge Graph Edge. This list is not
    ordered, nor is the order intended to convey any relationship
    between the edges that form this Auxiliary Graph.
    """

    attributes: list[Attribute]
    """Attributes of the Auxiliary Graph."""

    @override
    def hash(self) -> str:
        return tomhash(
            (frozenset(self.edges), frozenset(a.hash() for a in self.attributes))
        )

    def normalize(self, mapping: dict[EdgeID, EdgeID]) -> None:
        """Normalize the auxiliary graph given a mapping of old:new EdgeIDs."""
        self.edges = [mapping.get(edge_id, edge_id) for edge_id in self.edges]

    def update(self, other: AuxiliaryGraph) -> None:
        """Update the auxiliary graph in-place using the other."""
        if (not self.attributes) and other.attributes:
            self.attributes = other.attributes
        elif self.attributes and other.attributes:
            Attribute.merge_attribute_lists(self.attributes, other.attributes)

    @staticmethod
    def merge_dictionaries(old: AuxiliaryGraphsDict, new: AuxiliaryGraphsDict) -> None:
        """Merge the new auxiliary graphs into the existing auxiliary graphs."""
        for aux_id, graph in new.items():
            if aux_id in old:
                old[aux_id].update(graph)
            else:
                old[aux_id] = graph


AuxiliaryGraphsDict = dict[AuxGraphID, AuxiliaryGraph]
