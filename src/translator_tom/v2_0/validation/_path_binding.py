from __future__ import annotations

from typing import Any

from translator_tom.v2_0.models.auxiliary_graph import AuxiliaryGraphsDict
from translator_tom.v2_0.models.path_binding import PathBinding
from translator_tom.v2_0.validation._util import (
    Location,
    SemanticValidationResult,
    always_valid,
    extend_location,
    semantic_validate,
    validate_keys_exist,
)


@semantic_validate.register(PathBinding)
def _validate_path_binding(
    obj: PathBinding,
    location: Location | None = None,
    *,
    aux_graphs: AuxiliaryGraphsDict | None = None,
    **_: Any,
) -> SemanticValidationResult:
    if aux_graphs is None:
        return always_valid()
    return validate_keys_exist(
        obj.ids,
        aux_graphs.keys(),
        "Auxiliary graph",
        "auxiliary_graphs",
        extend_location(location, "ids"),
    )
