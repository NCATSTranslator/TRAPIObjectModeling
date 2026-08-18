from __future__ import annotations

from typing import Annotated

from pydantic import Field
from typing_extensions import override

from translator_tom.models.shared import AuxGraphID, EdgeID
from translator_tom.utils.object_base import TOMBase

__all__ = [
    "AuxiliaryGraph",
    "AuxiliaryGraphsDict",
]


class AuxiliaryGraph(TOMBase):
    """A single AuxiliaryGraph instance that is used by KnowledgeGraph Edges, Result Analysis support graphs, and PathBindings.

    Edges comprising an AuxiliaryGraph are a subset of the
    KnowledgeGraph in the message. Data creators can
    create an AuxiliaryGraph to assemble a specific collection
    of edges from the KnowledgeGraph into a named graph that can be
    referenced from an Edge as evidence/explanation supporting that Edge,
    from a Result Analysis as information used to generate a score, or
    from a PathBinding as the path for that Analysis.
    """

    edges: Annotated[list[EdgeID], Field(min_length=1)]
    """List of edges that form the AuxiliaryGraph.

    Each item is a reference to a single KnowledgeGraph Edge. This list is not
    ordered, nor is the order intended to convey any relationship
    between the edges that form this AuxiliaryGraph.
    """

    @override
    def _hash_repr(self) -> object:
        return frozenset(self.edges)

    def normalize(self, mapping: dict[EdgeID, EdgeID]) -> None:
        """Normalize the auxiliary graph given a mapping of old:new EdgeIDs."""
        self.edges = [mapping.get(edge_id, edge_id) for edge_id in self.edges]

    @staticmethod
    def normalize_aux_dict(
        auxiliary_graphs_dict: AuxiliaryGraphsDict, mapping: dict[EdgeID, EdgeID]
    ) -> None:
        """Normalize an AuxiliaryGraphsDict given a mapping of old:new EdgeIDs."""
        for auxg in auxiliary_graphs_dict.values():
            auxg.normalize(mapping)

    def update(self, other: AuxiliaryGraph) -> None:
        """Update the auxiliary graph in-place using the other."""
        new_edges = list(set(self.edges) | set(other.edges))
        self.edges.clear()
        self.edges.extend(new_edges)

    @staticmethod
    def merge_dictionaries(old: AuxiliaryGraphsDict, new: AuxiliaryGraphsDict) -> None:
        """Merge the new auxiliary graphs into the existing auxiliary graphs."""
        for aux_id, graph in new.items():
            if aux_id in old:
                old[aux_id].update(graph)
            else:
                old[aux_id] = graph


AuxiliaryGraphsDict = dict[AuxGraphID, AuxiliaryGraph]
