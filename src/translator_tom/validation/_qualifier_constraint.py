from __future__ import annotations

from typing import Any

from translator_tom.models.qualifier_constraint import QualifierConstraint
from translator_tom.validation._util import (
    Location,
    SemanticValidationResult,
    always_valid,
    semantic_validate,
)


@semantic_validate.register(QualifierConstraint)
def _validate_qualifier_constraint(  # pyright: ignore[reportUnusedFunction]
    obj: QualifierConstraint,  # pyright: ignore[reportUnusedParameter]
    location: Location | None = None,  # pyright: ignore[reportUnusedParameter]
    **kwargs: Any,  # pyright: ignore[reportUnusedParameter]
) -> SemanticValidationResult:
    return always_valid()
