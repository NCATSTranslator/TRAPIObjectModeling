from __future__ import annotations

import copy
from typing import Annotated

from pydantic import Field
from typing_extensions import override

from translator_tom.utils.object_base import TOMBase
from translator_tom.utils.shared import EdgeID, Infores, QNodeID
from translator_tom.v2_0.models.analysis import Analysis
from translator_tom.v2_0.models.node_binding import NodeBinding

__all__ = ["Result"]


class Result(TOMBase):
    """A Result object specifies the nodes and edges in the knowledge graph that satisfy the structure or conditions of a user-submitted query graph.

    It must contain a NodeBindings object (list of query graph node
    to knowledge graph node mappings) and a list of Analysis objects.
    """

    node_bindings: Annotated[dict[QNodeID, NodeBinding], Field(min_length=1)]
    """The dictionary of input QNodes to KnowledgeGraph Node bindings where the dictionary keys are the key identifiers of the QNodes and the associated values of those keys are instances of NodeBinding schema type (see below).

    Because a given QNode may have multiple KnowledgeGraph Nodes bound in the result,
    the NodeBinding object may list multiple KnowledgeGraph Nodes.
    """

    analyses: Annotated[list[Analysis], Field(min_length=1)] | None = None
    """The list of all Analysis components that contribute to the result.

    See below for Analysis components.
    """

    @property
    def analyses_list(self) -> list[Analysis]:
        """Get the analyses as a guaranteed list, even if they are represented as None."""
        return self.analyses if self.analyses is not None else []

    @override
    def _hash_repr(self) -> object:
        return {
            qnode_id: binding.hash() for qnode_id, binding in self.node_bindings.items()
        }

    def normalize(self, mapping: dict[EdgeID, EdgeID]) -> None:
        """Normalize the result given a mapping of old:new EdgeIDs."""
        for analysis in self.analyses_list:
            for binding in analysis.edge_bindings_dict.values():
                binding.ids = [mapping.get(edge_id, edge_id) for edge_id in binding.ids]

    @staticmethod
    def normalize_list(results: list[Result], mapping: dict[EdgeID, EdgeID]) -> None:
        """Normalize a result list given a mapping of old:new EdgeIDs."""
        for result in results:
            result.normalize(mapping)

    def update(self, other: Result) -> None:
        """Update the result in-place with another result."""
        if not other.analyses:
            return
        if not self.analyses:
            self.analyses = copy.deepcopy(other.analyses)
            return

        by_hash = {ana.hash(): ana for ana in self.analyses}
        for analysis in other.analyses:
            h = analysis.hash()
            existing = by_hash.get(h)
            if existing is not None:
                existing.update(analysis)
            else:
                new_analysis = copy.deepcopy(analysis)
                self.analyses.append(new_analysis)
                # register so a later same-hash analysis in `other` merges, not re-appends
                by_hash[h] = new_analysis

    @staticmethod
    def merge_results(
        results: list[Result], new: list[Result] | None = None
    ) -> list[Result]:
        """Merge the given results in-place.

        `new` is merged into `results`; pass a copy to preserve it.
        """
        if new is None:
            new = []
        merged = dict[str, Result]()
        for result in (*results, *new):
            result_hash = result.hash()
            if result_hash in merged:
                merged[result_hash].update(result)
            else:
                merged[result_hash] = result

        results.clear()
        results.extend(merged.values())
        return results

    def merge_analyses_by_resource_id(self) -> None:
        """Merge any of the analyses on this result by resource_id.

        Useful when a service unintentionally adds multiple analyses to a single result,
        Combines all of those analyses.
        """
        merged = dict[Infores, Analysis]()
        for analysis in self.analyses_list:
            existing = merged.get(analysis.resource_id)
            if existing is None:
                merged[analysis.resource_id] = analysis
            else:
                existing.update(analysis)

        self.analyses = list(merged.values()) or None
