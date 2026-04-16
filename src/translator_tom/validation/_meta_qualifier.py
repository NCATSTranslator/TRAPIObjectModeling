from __future__ import annotations

from typing import Any

from translator_tom.models.meta_qualifier import MetaQualifier
from translator_tom.validation._util import (
    Location,
    SemanticValidationResult,
    always_valid,
    semantic_validate,
)


@semantic_validate.register(MetaQualifier)
def _validate_meta_qualifier(  # pyright: ignore[reportUnusedFunction]
    obj: MetaQualifier,  # pyright: ignore[reportUnusedParameter]
    location: Location | None = None,  # pyright: ignore[reportUnusedParameter]
    **kwargs: Any,  # pyright: ignore[reportUnusedParameter]
) -> SemanticValidationResult:
    return always_valid()
