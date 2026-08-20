"""Converter for AuxiliaryGraph (attributes removed)."""

from __future__ import annotations

from typing import Any

from translator_tom.v1_6.models.auxiliary_graph import (
    AuxiliaryGraph as V16AuxiliaryGraph,
)
from translator_tom.v2_0.convert._util import _build, up_version
from translator_tom.v2_0.models.auxiliary_graph import AuxiliaryGraph


@up_version.register(V16AuxiliaryGraph)
def _convert_auxiliary_graph(obj: V16AuxiliaryGraph, **_: Any) -> AuxiliaryGraph:
    """Drop the removed `attributes`; keep `edges`."""
    data = obj.to_dict()
    data.pop("attributes", None)

    return _build(AuxiliaryGraph, data)
