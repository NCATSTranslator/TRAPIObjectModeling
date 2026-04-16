from __future__ import annotations

from typing import Any

from trapi_object_modeling.models.path_binding import PathBinding
from trapi_object_modeling.validation._util import (
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
    obj: PathBinding, location: Location | None = None, **kwargs: Any
) -> SemanticValidationResult:
    aux_graphs = kwargs.get("aux_graphs")

    if aux_graphs is not None and obj.id not in aux_graphs:
        return SemanticValidationWarningList(), [
            SemanticValidationError(
                f"Bound auxiliary graph `{obj.id}` is not present in auxiliary_graphs.",
                extend_location(location, "id"),
            )
        ]
    return always_valid()
