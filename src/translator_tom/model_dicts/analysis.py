from __future__ import annotations

import copy
from collections.abc import Mapping

from typing_extensions import NotRequired, TypedDict

from translator_tom.model_dicts.attribute import AttributeDict, AttributeDictUtil
from translator_tom.model_dicts.edge_binding import (
    EdgeBindingDict,
    EdgeBindingDictUtil,
)
from translator_tom.model_dicts.path_binding import (
    PathBindingDict,
    PathBindingDictUtil,
)
from translator_tom.models.analysis import Analysis, BaseAnalysis, PathfinderAnalysis
from translator_tom.models.shared import CURIE, AuxGraphID, QEdgeID, QPathID
from translator_tom.utils.dict_util_base import DictUtil, register_union_discriminator
from translator_tom.utils.hash import tomhash

__all__ = [
    "AnalysisDict",
    "AnalysisDictUtil",
    "BaseAnalysisDict",
    "BaseAnalysisDictUtil",
    "PathfinderAnalysisDict",
    "PathfinderAnalysisDictUtil",
]


class BaseAnalysisDict(TypedDict):
    resource_id: CURIE
    score: NotRequired[float | None]
    support_graphs: NotRequired[list[AuxGraphID] | None]
    scoring_method: NotRequired[str | None]
    attributes: NotRequired[list[AttributeDict] | None]


def _update_base(analysis: BaseAnalysisDict, other: BaseAnalysisDict) -> None:
    """Merge the shared BaseAnalysis fields (attributes, support graphs) in-place."""
    analysis_attrs = analysis.get("attributes")
    other_attrs = other.get("attributes")
    if (not analysis_attrs) and other_attrs:
        analysis["attributes"] = other_attrs
    elif analysis_attrs and other_attrs:
        AttributeDictUtil.merge_attribute_lists(analysis_attrs, other_attrs)

    analysis_sg = analysis.get("support_graphs")
    other_sg = other.get("support_graphs")
    if (not analysis_sg) and other_sg:
        analysis["support_graphs"] = other_sg
    elif analysis_sg and other_sg:
        analysis["support_graphs"] = list(set(analysis_sg) | set(other_sg))


class BaseAnalysisDictUtil(DictUtil[BaseAnalysisDict]):
    """Utility methods for `BaseAnalysisDict`, mirroring those on the `BaseAnalysis` model."""

    _model = BaseAnalysis

    @staticmethod
    def support_graphs_list(analysis: BaseAnalysisDict) -> list[AuxGraphID]:
        """Get the support graphs as a guaranteed list, even if they are represented as None."""
        support_graphs = analysis.get("support_graphs")
        return support_graphs if support_graphs is not None else []

    @staticmethod
    def attributes_list(analysis: BaseAnalysisDict) -> list[AttributeDict]:
        """Get the attributes as a guaranteed list, even if they are represented as None."""
        attributes = analysis.get("attributes")
        return attributes if attributes is not None else []

    @classmethod
    def hash(cls, obj: BaseAnalysisDict) -> str:
        """Hash matching `BaseAnalysis.hash` (resource, score, support graphs, method)."""
        return tomhash(
            (
                obj["resource_id"],
                obj.get("score"),
                frozenset(cls.support_graphs_list(obj)),
                obj.get("scoring_method"),
            )
        )


class AnalysisDict(BaseAnalysisDict):
    edge_bindings: dict[QEdgeID, list[EdgeBindingDict]]


class AnalysisDictUtil(DictUtil[AnalysisDict]):
    """Utility methods for `AnalysisDict`, mirroring those on the `Analysis` model."""

    _model = Analysis

    @classmethod
    def hash(cls, obj: AnalysisDict) -> str:
        """Hash matching `Analysis.hash` (base analysis plus edge bindings)."""
        return tomhash(
            (
                BaseAnalysisDictUtil.hash(obj),
                {
                    qedge_id: frozenset(EdgeBindingDictUtil.hash(b) for b in bindings)
                    for qedge_id, bindings in obj["edge_bindings"].items()
                },
            )
        )

    @staticmethod
    def update(analysis: AnalysisDict, other: AnalysisDict) -> None:
        """Update the analysis in-place with another analysis."""
        _update_base(analysis, other)
        for k in other["edge_bindings"]:
            if k in analysis["edge_bindings"]:
                # Dedupe by hash, existing bindings win
                merged = {
                    EdgeBindingDictUtil.hash(b): b for b in analysis["edge_bindings"][k]
                }
                for b in other["edge_bindings"][k]:
                    merged.setdefault(EdgeBindingDictUtil.hash(b), copy.deepcopy(b))
                analysis["edge_bindings"][k] = list(merged.values())
            else:
                analysis["edge_bindings"][k] = copy.deepcopy(other["edge_bindings"][k])


class PathfinderAnalysisDict(BaseAnalysisDict):
    path_bindings: dict[QPathID, list[PathBindingDict]]


class PathfinderAnalysisDictUtil(DictUtil[PathfinderAnalysisDict]):
    """Utility methods for `PathfinderAnalysisDict`, mirroring the `PathfinderAnalysis` model."""

    _model = PathfinderAnalysis

    @classmethod
    def hash(cls, obj: PathfinderAnalysisDict) -> str:
        """Hash matching `PathfinderAnalysis.hash` (base analysis plus path bindings)."""
        return tomhash(
            (
                BaseAnalysisDictUtil.hash(obj),
                {
                    qpath_id: frozenset(PathBindingDictUtil.hash(b) for b in bindings)
                    for qpath_id, bindings in obj["path_bindings"].items()
                },
            )
        )

    @staticmethod
    def update(analysis: PathfinderAnalysisDict, other: PathfinderAnalysisDict) -> None:
        """Update the analysis in-place with another analysis."""
        _update_base(analysis, other)
        for k in other["path_bindings"]:
            if k in analysis["path_bindings"]:
                # Dedupe by hash, existing bindings win
                merged = {
                    PathBindingDictUtil.hash(b): b for b in analysis["path_bindings"][k]
                }
                for b in other["path_bindings"][k]:
                    merged.setdefault(PathBindingDictUtil.hash(b), copy.deepcopy(b))
                analysis["path_bindings"][k] = list(merged.values())
            else:
                analysis["path_bindings"][k] = copy.deepcopy(other["path_bindings"][k])


def _discriminate_analysis(
    value: Mapping[str, object],
) -> type[Analysis | PathfinderAnalysis]:
    """Pick the concrete analysis model for a raw dict (`path_bindings` -> Pathfinder)."""
    return PathfinderAnalysis if "path_bindings" in value else Analysis


# `Result.analyses` is an `Analysis | PathfinderAnalysis` union with no pydantic
# discriminator. `Result.hash` ignores `analyses`, so this isn't hit by base hashing
# today, but register it so any future base-hashed use resolves correctly.
register_union_discriminator((Analysis, PathfinderAnalysis), _discriminate_analysis)
