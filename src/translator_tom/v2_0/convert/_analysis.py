"""Converters for the Analysis family (Base/Pathfinder collapse + binding reshape)."""

from __future__ import annotations

from typing import Any

from translator_tom.v1_6.models.analysis import Analysis as V16Analysis
from translator_tom.v1_6.models.analysis import BaseAnalysis as V16BaseAnalysis
from translator_tom.v1_6.models.analysis import (
    PathfinderAnalysis as V16PathfinderAnalysis,
)
from translator_tom.v2_0.convert._util import _build, _collapse_bindings, up_version
from translator_tom.v2_0.models.analysis import Analysis


@up_version.register(V16BaseAnalysis)
def _convert_base_analysis(obj: V16BaseAnalysis, **_: Any) -> Analysis:
    """A bare BaseAnalysis (no bindings) → the unified Analysis."""
    return _build(Analysis, obj.to_dict())


@up_version.register(V16Analysis)
def _convert_analysis(obj: V16Analysis, **_: Any) -> Analysis:
    """Collapse edge_bindings from list-per-key to a single binding with `ids`."""
    data = obj.to_dict()

    edge_bindings = _collapse_bindings(obj.edge_bindings)
    if edge_bindings is not None:
        data["edge_bindings"] = edge_bindings
    else:
        data.pop("edge_bindings", None)

    return _build(Analysis, data)


@up_version.register(V16PathfinderAnalysis)
def _convert_pathfinder_analysis(obj: V16PathfinderAnalysis, **_: Any) -> Analysis:
    """Collapse path_bindings onto the unified Analysis class."""
    data = obj.to_dict()

    path_bindings = _collapse_bindings(obj.path_bindings)
    if path_bindings is not None:
        data["path_bindings"] = path_bindings
    else:
        data.pop("path_bindings", None)

    return _build(Analysis, data)
