"""Converters for the standalone binding models."""

from __future__ import annotations

from typing import Any

from translator_tom.v1_6.models.edge_binding import EdgeBinding as V16EdgeBinding
from translator_tom.v1_6.models.node_binding import NodeBinding as V16NodeBinding
from translator_tom.v1_6.models.path_binding import PathBinding as V16PathBinding
from translator_tom.v2_0.convert._util import up_version
from translator_tom.v2_0.models.edge_binding import EdgeBinding
from translator_tom.v2_0.models.node_binding import NodeBinding
from translator_tom.v2_0.models.path_binding import PathBinding


@up_version.register(V16NodeBinding)
def _convert_node_binding(obj: V16NodeBinding, **_: Any) -> NodeBinding:
    """Convert a lone NodeBinding (drops the removed query_id/attributes)."""
    return NodeBinding(ids=[obj.id])


@up_version.register(V16EdgeBinding)
def _convert_edge_binding(obj: V16EdgeBinding, **_: Any) -> EdgeBinding:
    """Convert a lone EdgeBinding (drops the removed attributes)."""
    return EdgeBinding(ids=[obj.id])


@up_version.register(V16PathBinding)
def _convert_path_binding(obj: V16PathBinding, **_: Any) -> PathBinding:
    """Convert a lone PathBinding (single `id` → `ids`)."""
    return PathBinding(ids=[obj.id])
