from __future__ import annotations

import itertools
from typing import Annotated, override

from pydantic import Field

from translator_tom.models.analysis import Analysis, PathfinderAnalysis
from translator_tom.models.node_binding import NodeBinding
from translator_tom.models.shared import EdgeID, Infores, QNodeID
from translator_tom.utils.hash import tomhash
from translator_tom.utils.object_base import TOMBase

__all__ = ["Result"]


class Result(TOMBase):
    """A Result object specifies the nodes and edges in the knowledge graph that satisfy the structure or conditions of a user-submitted query graph.

    It must contain a NodeBindings object (list of query graph node
    to knowledge graph node mappings) and a list of Analysis objects.
    """

    node_bindings: dict[QNodeID, Annotated[list[NodeBinding], Field(min_length=1)]]
    """The dictionary of Input Query Graph to Result Knowledge Graph node bindings where the dictionary keys are the key identifiers of the Query Graph nodes and the associated values of those keys are instances of NodeBinding schema type (see below).

    This value is an array of NodeBindings since a given query node may have multiple
    knowledge graph Node bindings in the result.
    """

    analyses: list[Analysis | PathfinderAnalysis]
    """The list of all Analysis components that contribute to the result."""

    @override
    def hash(self) -> str:
        return tomhash(
            {
                qnode_id: frozenset(b.hash() for b in bindings)
                for qnode_id, bindings in self.node_bindings.items()
            }
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
            self.analyses = other.analyses
            return

        by_hash = {ana.hash(): ana for ana in self.analyses}
        for analysis in other.analyses:
            existing = by_hash.get(analysis.hash())
            if existing is not None:
                existing.update(analysis)  # pyright:ignore[reportArgumentType] Equality means they're the same type
            else:
                self.analyses.append(analysis)

    @staticmethod
    def merge_results(
        results: list[Result], new: list[Result] | None = None
    ) -> list[Result]:
        """Merge the given results in-place.

        If new results are provided, merge them into the first list.
        Does not mutate `new`.
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
        merged: dict[
            tuple[type[Analysis | PathfinderAnalysis], Infores],
            Analysis | PathfinderAnalysis,
        ] = {}
        for analysis in self.analyses:
            key = (type(analysis), analysis.resource_id)
            existing = merged.get(key)
            if existing is None:
                merged[key] = analysis
            else:
                existing.update(analysis)  # pyright:ignore[reportArgumentType] key includes type, so they match

        self.analyses = list(merged.values())
