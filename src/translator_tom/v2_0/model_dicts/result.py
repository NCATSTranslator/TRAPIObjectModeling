from __future__ import annotations

import copy

from typing_extensions import NotRequired, TypedDict

from translator_tom.utils.dict_util_base import DictUtil
from translator_tom.utils.hash import tomhash
from translator_tom.utils.shared import CURIE, EdgeID, QNodeID
from translator_tom.v2_0.model_dicts.analysis import AnalysisDict, AnalysisDictUtil
from translator_tom.v2_0.model_dicts.node_binding import (
    NodeBindingDict,
    NodeBindingDictUtil,
)
from translator_tom.v2_0.models.result import Result

__all__ = ["ResultDict", "ResultDictUtil"]


class ResultDict(TypedDict):
    node_bindings: dict[QNodeID, NodeBindingDict]
    analyses: NotRequired[list[AnalysisDict] | None]


class ResultDictUtil(DictUtil[ResultDict]):
    """Utility methods for `ResultDict`, mirroring those on the `Result` model."""

    _model = Result

    @staticmethod
    def analyses_list(result: ResultDict) -> list[AnalysisDict]:
        """Get the analyses as a guaranteed list, even if they are represented as None."""
        analyses = result.get("analyses")
        return analyses if analyses is not None else []

    @classmethod
    def hash(cls, obj: ResultDict) -> str:
        """Hash matching `Result.hash` (node bindings only)."""
        return tomhash(
            {
                qnode_id: NodeBindingDictUtil.hash(binding)
                for qnode_id, binding in obj["node_bindings"].items()
            }
        )

    @staticmethod
    def normalize(result: ResultDict, mapping: dict[EdgeID, EdgeID]) -> None:
        """Normalize the result given a mapping of old:new EdgeIDs."""
        for analysis in ResultDictUtil.analyses_list(result):
            for binding in AnalysisDictUtil.edge_bindings_dict(analysis).values():
                binding["ids"] = [
                    mapping.get(edge_id, edge_id) for edge_id in binding["ids"]
                ]

    @staticmethod
    def normalize_list(
        results: list[ResultDict], mapping: dict[EdgeID, EdgeID]
    ) -> None:
        """Normalize a result list given a mapping of old:new EdgeIDs."""
        for result in results:
            ResultDictUtil.normalize(result, mapping)

    @staticmethod
    def update(result: ResultDict, other: ResultDict) -> None:
        """Update the result in-place with another result."""
        other_analyses = other.get("analyses")
        if not other_analyses:
            return
        result_analyses = result.get("analyses")
        if not result_analyses:
            result["analyses"] = copy.deepcopy(other_analyses)
            return

        by_hash = {AnalysisDictUtil.hash(ana): ana for ana in result_analyses}
        for analysis in other_analyses:
            h = AnalysisDictUtil.hash(analysis)
            existing = by_hash.get(h)
            if existing is not None:
                AnalysisDictUtil.update(existing, analysis)
            else:
                new_analysis = copy.deepcopy(analysis)
                result_analyses.append(new_analysis)
                # register so a later same-hash analysis in `other` merges, not re-appends
                by_hash[h] = new_analysis

    @staticmethod
    def merge_results(
        results: list[ResultDict], new: list[ResultDict] | None = None
    ) -> list[ResultDict]:
        """Merge the given results in-place.

        `new` is merged into (and aliased by) `results`; pass a copy to preserve it.
        """
        if new is None:
            new = []
        merged = dict[str, ResultDict]()
        for result in (*results, *new):
            result_hash = ResultDictUtil.hash(result)
            if result_hash in merged:
                ResultDictUtil.update(merged[result_hash], result)
            else:
                merged[result_hash] = result

        results.clear()
        results.extend(merged.values())
        return results

    @staticmethod
    def merge_analyses_by_resource_id(result: ResultDict) -> None:
        """Merge any of the analyses on this result by resource_id.

        Useful when a service unintentionally adds multiple analyses to a single result,
        combining all of those analyses.
        """
        merged = dict[CURIE, AnalysisDict]()
        for analysis in ResultDictUtil.analyses_list(result):
            existing = merged.get(analysis["resource_id"])
            if existing is None:
                merged[analysis["resource_id"]] = analysis
            else:
                AnalysisDictUtil.update(existing, analysis)

        result["analyses"] = list(merged.values()) or None
