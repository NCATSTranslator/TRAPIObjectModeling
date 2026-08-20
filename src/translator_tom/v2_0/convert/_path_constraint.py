"""Converter for PathConstraint (field rename)."""

from __future__ import annotations

from typing import Any

from translator_tom.v1_6.models.path_constraint import (
    PathConstraint as V16PathConstraint,
)
from translator_tom.v2_0.convert._util import _build, up_version
from translator_tom.v2_0.models.path_constraint import PathConstraint


@up_version.register(V16PathConstraint)
def _convert_path_constraint(obj: V16PathConstraint, **_: Any) -> PathConstraint:
    """Rename intermediate_categories → required_intermediate_categories."""
    data = obj.to_dict()

    categories = data.pop("intermediate_categories", None)
    if categories is not None:
        data["required_intermediate_categories"] = categories

    return _build(PathConstraint, data)
