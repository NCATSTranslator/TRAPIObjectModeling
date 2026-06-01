from __future__ import annotations

from typing_extensions import TypedDict

from translator_tom.model_dicts.analysis import AnalysisDict, PathfinderAnalysisDict
from translator_tom.model_dicts.node_binding import NodeBindingDict
from translator_tom.models.shared import QNodeID

__all__ = ["ResultDict"]


class ResultDict(TypedDict):
    node_bindings: dict[QNodeID, list[NodeBindingDict]]
    analyses: list[AnalysisDict | PathfinderAnalysisDict]
