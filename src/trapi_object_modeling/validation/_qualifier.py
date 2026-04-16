from __future__ import annotations

from typing import Any

from trapi_object_modeling.models.qualifier import Qualifier
from trapi_object_modeling.validation._util import (
    Location,
    SemanticValidationResult,
    always_valid,
    semantic_validate,
)


@semantic_validate.register(Qualifier)
def _validate_qualifier(  # pyright: ignore[reportUnusedFunction]
    obj: Qualifier,  # pyright: ignore[reportUnusedParameter]
    location: Location | None = None,  # pyright: ignore[reportUnusedParameter]
    **kwargs: Any,  # pyright: ignore[reportUnusedParameter]
) -> SemanticValidationResult:
    return always_valid()
