from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from translator_tom.model_dicts.attribute import AttributeDict
from translator_tom.model_dicts.edge_binding import EdgeBindingDict
from translator_tom.model_dicts.path_binding import PathBindingDict
from translator_tom.models.shared import CURIE, AuxGraphID, QEdgeID, QPathID

__all__ = [
    "AnalysisDict",
    "BaseAnalysisDict",
    "PathfinderAnalysisDict",
]


class BaseAnalysisDict(TypedDict):
    resource_id: CURIE
    score: NotRequired[float | None]
    support_graphs: NotRequired[list[AuxGraphID] | None]
    scoring_method: NotRequired[str | None]
    attributes: NotRequired[list[AttributeDict] | None]


class AnalysisDict(BaseAnalysisDict):
    edge_bindings: dict[QEdgeID, list[EdgeBindingDict]]


class PathfinderAnalysisDict(BaseAnalysisDict):
    path_bindings: dict[QPathID, list[PathBindingDict]]
