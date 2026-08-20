"""Converter for Result (node_binding reshape + analyses)."""

from __future__ import annotations

from typing import Any

from translator_tom.v1_6.models.result import Result as V16Result
from translator_tom.v2_0.convert._util import _binding_dedup, _build, up_version
from translator_tom.v2_0.models.result import Result


@up_version.register(V16Result)
def _convert_result(obj: V16Result, **kwargs: Any) -> Result:
    """Collapse each node_binding list into a single binding; convert analyses."""
    data = obj.to_dict()

    data["node_bindings"] = {
        qnode_id: {"ids": _binding_dedup(binding.id for binding in bindings)}
        for qnode_id, bindings in obj.node_bindings.items()
    }

    if obj.analyses:
        data["analyses"] = [
            up_version(analysis, **kwargs).to_dict() for analysis in obj.analyses
        ]
    else:
        data.pop("analyses", None)

    return _build(Result, data)
