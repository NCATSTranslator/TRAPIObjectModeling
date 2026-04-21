from __future__ import annotations

import itertools
from typing import Annotated, override

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass
from stablehash import stablehash

from translator_tom.models.analysis import Analysis, PathfinderAnalysis
from translator_tom.models.node_binding import NodeBinding
from translator_tom.models.shared import EdgeID, Infores, QNodeID
from translator_tom.utils.object_base import TOMBaseObject


@dataclass(kw_only=True, config=ConfigDict(extra="allow"), eq=False)
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
    def hash(self) -> str:
        return stablehash(
            {
                qnode_id: frozenset(bindings)
                for qnode_id, bindings in self.node_bindings.items()
            }
        ).hexdigest()

    def normalize(self, mapping: dict[EdgeID, EdgeID]) -> None:
        """Normalize the result given a mapping of old:new EdgeIDs."""
        for analysis in self.analyses:
            if not isinstance(analysis, Analysis):
                continue
            for binding in itertools.chain(
                *(bindings for bindings in analysis.edge_bindings.values())
            ):
                binding.id = mapping.get(binding.id, binding.id)

    def update(self, other: Result) -> None:
        """Update the result in-place with another result."""
        if not other.analyses:
            return
        if (not self.analyses) and other.analyses:
            self.analyses = other.analyses
            return

        for analysis in other.analyses:
            not_present = True
            for ana in self.analyses:
                if analysis == ana:
                    ana.update(analysis)  # pyright:ignore[reportArgumentType] Equality means they're the same type
                    not_present = False
            if not_present:
                self.analyses.append(analysis)
