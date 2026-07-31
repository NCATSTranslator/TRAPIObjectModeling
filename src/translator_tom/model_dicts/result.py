from __future__ import annotations

import itertools
from typing import cast

from typing_extensions import TypedDict

from translator_tom.model_dicts.analysis import (
    AnalysisDict,
    AnalysisDictUtil,
    PathfinderAnalysisDict,
    PathfinderAnalysisDictUtil,
)
from translator_tom.model_dicts.node_binding import (
    NodeBindingDict,
    NodeBindingDictUtil,
)
from translator_tom.models.result import Result
from translator_tom.models.shared import CURIE, EdgeID, QNodeID
from translator_tom.utils.dict_util_base import DictUtil
from translator_tom.utils.hash import tomhash

__all__ = ["ResultDict", "ResultDictUtil"]


class ResultDict(TypedDict):
    node_bindings: dict[QNodeID, list[NodeBindingDict]]
    analyses: list[AnalysisDict | PathfinderAnalysisDict]


def _analysis_hash(analysis: AnalysisDict | PathfinderAnalysisDict) -> str:
    """Hash an analysis dict, dispatching on its structural shape."""
    if "path_bindings" in analysis:
        return PathfinderAnalysisDictUtil.hash(cast("PathfinderAnalysisDict", analysis))
    return AnalysisDictUtil.hash(analysis)


def _update_analysis(
    existing: AnalysisDict | PathfinderAnalysisDict,
    other: AnalysisDict | PathfinderAnalysisDict,
) -> None:
    """Update one analysis dict with another of the same structural shape."""
    if "path_bindings" in existing:
        PathfinderAnalysisDictUtil.update(
            cast("PathfinderAnalysisDict", existing),
            cast("PathfinderAnalysisDict", other),
        )
    else:
        AnalysisDictUtil.update(existing, cast("AnalysisDict", other))


class ResultDictUtil(DictUtil[ResultDict]):
    """Utility methods for `ResultDict`, mirroring those on the `Result` model."""

    _model = Result

    @classmethod
    def hash(cls, obj: ResultDict) -> str:
        """Hash matching `Result.hash` (node bindings only)."""
        return tomhash(
            {
                qnode_id: frozenset(NodeBindingDictUtil.hash(b) for b in bindings)
                for qnode_id, bindings in obj["node_bindings"].items()
            }
        )

    @staticmethod
    def normalize(result: ResultDict, mapping: dict[EdgeID, EdgeID]) -> None:
        """Normalize the result given a mapping of old:new EdgeIDs."""
        for analysis in result["analyses"]:
            if "edge_bindings" not in analysis:
                continue
            analysis = cast("AnalysisDict", analysis)
            for binding in itertools.chain(
                *(bindings for bindings in analysis["edge_bindings"].values())
            ):
                binding["id"] = mapping.get(binding["id"], binding["id"])

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
        if not other["analyses"]:
            return
        if not result["analyses"]:
            result["analyses"] = other["analyses"]
            return

        by_hash = {_analysis_hash(ana): ana for ana in result["analyses"]}
        for analysis in other["analyses"]:
            existing = by_hash.get(_analysis_hash(analysis))
            if existing is not None:
                _update_analysis(existing, analysis)
            else:
                result["analyses"].append(analysis)

    @staticmethod
    def merge_results(
        results: list[ResultDict], new: list[ResultDict] | None = None
    ) -> list[ResultDict]:
        """Merge the given results in-place.

        If new results are provided, merge them into the first list.
        Does not mutate `new`.
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
        merged: dict[tuple[bool, CURIE], AnalysisDict | PathfinderAnalysisDict] = {}
        for analysis in result["analyses"]:
            # The bool distinguishes Analysis vs PathfinderAnalysis (mirrors the
            # model keying by type), so only same-shape analyses ever merge.
            key = ("path_bindings" in analysis, analysis["resource_id"])
            existing = merged.get(key)
            if existing is None:
                merged[key] = analysis
            else:
                _update_analysis(existing, analysis)

        result["analyses"] = list(merged.values())
