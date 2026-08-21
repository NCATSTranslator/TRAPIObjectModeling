"""Transform for the Analysis family (Base/Pathfinder collapse + binding reshape)."""

from __future__ import annotations

from typing import Any

from translator_tom.v1_6.models.analysis import Analysis as V16Analysis
from translator_tom.v1_6.models.analysis import BaseAnalysis as V16BaseAnalysis
from translator_tom.v1_6.models.analysis import (
    PathfinderAnalysis as V16PathfinderAnalysis,
)
from translator_tom.v2_0.convert._util import _collapse_bindings, register
from translator_tom.v2_0.models.analysis import Analysis


@register(V16BaseAnalysis, Analysis)
@register(V16Analysis, Analysis)
@register(V16PathfinderAnalysis, Analysis)
def _upgrade_analysis(data: dict[str, Any], **_: Any) -> dict[str, Any]:
    """Collapse binding maps (list→single `{ids}`) onto the unified Analysis.

    A 1.6 base/regular/pathfinder analysis all become one 2.0 Analysis; whichever of
    `edge_bindings`/`path_bindings` is present is collapsed, the other stays absent.
    """
    data = dict(data)

    for key in ("edge_bindings", "path_bindings"):
        bindings = data.get(key)
        if bindings is None:
            continue
        collapsed = _collapse_bindings(bindings)
        if collapsed is not None:
            data[key] = collapsed
        else:
            data.pop(key, None)

    return data
