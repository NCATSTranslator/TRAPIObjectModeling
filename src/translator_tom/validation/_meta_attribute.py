from __future__ import annotations

from typing import Any

from translator_tom.models.meta_attribute import MetaAttribute
from translator_tom.validation._util import (
    Location,
    SemanticValidationResult,
    always_valid,
    semantic_validate,
)


@semantic_validate.register(MetaAttribute)
def _validate_meta_attribute(  # pyright: ignore[reportUnusedFunction]
    obj: MetaAttribute,  # pyright: ignore[reportUnusedParameter]
    location: Location | None = None,  # pyright: ignore[reportUnusedParameter]
    **kwargs: Any,  # pyright: ignore[reportUnusedParameter]
) -> SemanticValidationResult:
    return always_valid()
