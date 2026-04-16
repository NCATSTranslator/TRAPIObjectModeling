from __future__ import annotations

from typing import Annotated

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from translator_tom.models.attribute import Attribute
from translator_tom.models.shared import AuxGraphID, EdgeID
from translator_tom.utils.object_base import TOMBaseObject


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

    def normalize(self, mapping: dict[EdgeID, EdgeID]) -> None:
        """Normalize the auxiliary graph given a mapping of old:new EdgeIDs."""
        self.edges = [mapping.get(edge_id, edge_id) for edge_id in self.edges]


AuxiliaryGraphsDict = dict[AuxGraphID, AuxiliaryGraph]
