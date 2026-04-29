from __future__ import annotations

from typing import Any

from translator_tom.models.auxiliary_graph import AuxiliaryGraphsDict
from translator_tom.models.path_binding import PathBinding
from translator_tom.validation._util import (
    Location,
    SemanticValidationError,
    SemanticValidationResult,
    SemanticValidationWarningList,
    always_valid,
    extend_location,
    semantic_validate,
)


@semantic_validate.register(PathBinding)
def _validate_path_binding(  # pyright: ignore[reportUnusedFunction]
    obj: PathBinding,
    location: Location | None = None,
    *,
    aux_graphs: AuxiliaryGraphsDict | None = None,
    **_: Any,
) -> SemanticValidationResult:
    if aux_graphs is not None and obj.id not in aux_graphs:
        return SemanticValidationWarningList(), [
            SemanticValidationError(
                f"Bound auxiliary graph `{obj.id}` is not present in auxiliary_graphs.",
                extend_location(location, "id"),
            )
        ]
    return always_valid()
