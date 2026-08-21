"""Transform for PathConstraint (field rename)."""

from __future__ import annotations

from typing import Any

from translator_tom.v1_6.models.path_constraint import (
    PathConstraint as V16PathConstraint,
)
from translator_tom.v2_0.convert._util import register
from translator_tom.v2_0.models.path_constraint import PathConstraint


@register(V16PathConstraint, PathConstraint)
def _upgrade_path_constraint(data: dict[str, Any], **_: Any) -> dict[str, Any]:
    """Rename intermediate_categories → required_intermediate_categories."""
    data = dict(data)

    categories = data.pop("intermediate_categories", None)
    if categories is not None:
        data["required_intermediate_categories"] = categories

    return data
