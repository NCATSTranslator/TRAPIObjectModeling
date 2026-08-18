from __future__ import annotations

import copy
from typing import TypeVar

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
from translator_tom.models.analysis import Analysis
from translator_tom.models.shared import CURIE, AuxGraphID, QEdgeID, QPathID
from translator_tom.utils.dict_util_base import DictUtil
from translator_tom.utils.hash import tomhash

__all__ = ["AnalysisDict", "AnalysisDictUtil"]

_BindingDictT = TypeVar("_BindingDictT", EdgeBindingDict, PathBindingDict)


class AnalysisDict(TypedDict):
    resource_id: CURIE
    edge_bindings: NotRequired[dict[QEdgeID, EdgeBindingDict] | None]
    path_bindings: NotRequired[dict[QPathID, PathBindingDict] | None]
    score: NotRequired[float | None]
    support_graphs: NotRequired[list[AuxGraphID] | None]
    scoring_method: NotRequired[str | None]
    attributes: NotRequired[list[AttributeDict] | None]


class AnalysisDictUtil(DictUtil[AnalysisDict]):
    """Utility methods for `AnalysisDict`, mirroring those on the `Analysis` model."""

    _model = Analysis

    @staticmethod
    def edge_bindings_dict(analysis: AnalysisDict) -> dict[QEdgeID, EdgeBindingDict]:
        """Get the edge_bindings as a guaranteed dict, even if they are represented as None."""
        edge_bindings = analysis.get("edge_bindings")
        return edge_bindings if edge_bindings is not None else {}

    @staticmethod
    def path_bindings_dict(analysis: AnalysisDict) -> dict[QPathID, PathBindingDict]:
        """Get the path_bindings as a guaranteed dict, even if they are represented as None."""
        path_bindings = analysis.get("path_bindings")
        return path_bindings if path_bindings is not None else {}

    @staticmethod
    def support_graphs_list(analysis: AnalysisDict) -> list[AuxGraphID]:
        """Get the support graphs as a guaranteed list, even if they are represented as None."""
        support_graphs = analysis.get("support_graphs")
        return support_graphs if support_graphs is not None else []

    @staticmethod
    def attributes_list(analysis: AnalysisDict) -> list[AttributeDict]:
        """Get the attributes as a guaranteed list, even if they are represented as None."""
        attributes = analysis.get("attributes")
        return attributes if attributes is not None else []

    @classmethod
    def hash(cls, obj: AnalysisDict) -> str:
        """Hash matching `Analysis.hash` (scalars, support graphs, both binding maps)."""
        return tomhash(
            (
                obj["resource_id"],
                obj.get("score"),
                frozenset(cls.support_graphs_list(obj)),
                obj.get("scoring_method"),
                {
                    qedge_id: EdgeBindingDictUtil.hash(binding)
                    for qedge_id, binding in cls.edge_bindings_dict(obj).items()
                },
                {
                    qpath_id: PathBindingDictUtil.hash(binding)
                    for qpath_id, binding in cls.path_bindings_dict(obj).items()
                },
            )
        )

    @staticmethod
    def update(analysis: AnalysisDict, other: AnalysisDict) -> None:
        """Update the analysis in-place with another analysis."""
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

        other_eb = other.get("edge_bindings")
        if other_eb:
            analysis_eb = analysis.get("edge_bindings")
            if analysis_eb is None:
                analysis["edge_bindings"] = copy.deepcopy(other_eb)
            else:
                AnalysisDictUtil._merge_binding_map(analysis_eb, other_eb)

        other_pb = other.get("path_bindings")
        if other_pb:
            analysis_pb = analysis.get("path_bindings")
            if analysis_pb is None:
                analysis["path_bindings"] = copy.deepcopy(other_pb)
            else:
                AnalysisDictUtil._merge_binding_map(analysis_pb, other_pb)

    @staticmethod
    def _merge_binding_map(
        target: dict[str, _BindingDictT], other: dict[str, _BindingDictT]
    ) -> None:
        """Merge `other` into `target` in-place, unioning each binding's ids per key."""
        for key, binding in other.items():
            existing = target.get(key)
            if existing is None:
                target[key] = copy.deepcopy(binding)
            else:
                # ids identify a set of KG edges/aux graphs; union, deduped, order-stable.
                existing["ids"] = list(
                    dict.fromkeys((*existing["ids"], *binding["ids"]))
                )
