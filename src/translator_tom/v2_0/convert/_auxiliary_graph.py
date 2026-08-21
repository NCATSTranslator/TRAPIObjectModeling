"""Transform for AuxiliaryGraph (attributes removed)."""

from __future__ import annotations

from typing import Any

from translator_tom.v1_6.models.auxiliary_graph import (
    AuxiliaryGraph as V16AuxiliaryGraph,
)
from translator_tom.v2_0.convert._util import register
from translator_tom.v2_0.models.auxiliary_graph import AuxiliaryGraph


@register(V16AuxiliaryGraph, AuxiliaryGraph)
def _upgrade_auxiliary_graph(data: dict[str, Any], **_: Any) -> dict[str, Any]:
    """Drop the removed `attributes`; keep `edges`."""
    data = dict(data)
    data.pop("attributes", None)

    return data
