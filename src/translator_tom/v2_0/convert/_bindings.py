"""Transforms for the standalone binding models."""

from __future__ import annotations

from typing import Any

from translator_tom.v1_6.models.edge_binding import EdgeBinding as V16EdgeBinding
from translator_tom.v1_6.models.node_binding import NodeBinding as V16NodeBinding
from translator_tom.v1_6.models.path_binding import PathBinding as V16PathBinding
from translator_tom.v2_0.convert._util import register
from translator_tom.v2_0.models.edge_binding import EdgeBinding
from translator_tom.v2_0.models.node_binding import NodeBinding
from translator_tom.v2_0.models.path_binding import PathBinding


@register(V16NodeBinding, NodeBinding)
def _upgrade_node_binding(data: dict[str, Any], **_: Any) -> dict[str, Any]:
    """Convert a lone NodeBinding (drops the removed query_id/attributes)."""
    return {"ids": [data["id"]]}


@register(V16EdgeBinding, EdgeBinding)
def _upgrade_edge_binding(data: dict[str, Any], **_: Any) -> dict[str, Any]:
    """Convert a lone EdgeBinding (drops the removed attributes)."""
    return {"ids": [data["id"]]}


@register(V16PathBinding, PathBinding)
def _upgrade_path_binding(data: dict[str, Any], **_: Any) -> dict[str, Any]:
    """Convert a lone PathBinding (single `id` → `ids`)."""
    return {"ids": [data["id"]]}
