from __future__ import annotations

from typing import Any

from translator_tom.models.qualifier import Qualifier, QualifierConstraint
from translator_tom.validation._util import (
    Location,
    SemanticValidationResult,
    always_valid,
    semantic_validate,
)


@semantic_validate.register(Qualifier)
def _validate_qualifier(
    obj: Qualifier,
    location: Location | None = None,
    **_: Any,
) -> SemanticValidationResult:
    return always_valid()


@semantic_validate.register(QualifierConstraint)
def _validate_qualifier_constraint(
    obj: QualifierConstraint,
    location: Location | None = None,
    **_: Any,
) -> SemanticValidationResult:
    return always_valid()
