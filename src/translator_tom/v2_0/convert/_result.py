"""Transform for Result (node_binding reshape + analyses)."""

from __future__ import annotations

from typing import Any

from translator_tom.v1_6.models.result import Result as V16Result
from translator_tom.v2_0.convert._analysis import _upgrade_analysis
from translator_tom.v2_0.convert._util import _binding_dedup, register
from translator_tom.v2_0.models.result import Result


@register(V16Result, Result)
def _upgrade_result(data: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Collapse each node_binding list into a single `{ids}`; convert analyses."""
    data = dict(data)

    node_bindings = data.get("node_bindings")
    if node_bindings:
        data["node_bindings"] = {
            qnode_id: {"ids": _binding_dedup(binding["id"] for binding in bindings)}
            for qnode_id, bindings in node_bindings.items()
        }

    analyses = data.get("analyses")
    if analyses:
        data["analyses"] = [
            _upgrade_analysis(analysis, **kwargs) for analysis in analyses
        ]
    else:
        data.pop("analyses", None)

    return data
