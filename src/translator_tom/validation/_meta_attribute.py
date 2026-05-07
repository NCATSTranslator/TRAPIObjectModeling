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
def _validate_meta_attribute(
    obj: MetaAttribute,
    location: Location | None = None,
    **_: Any,
) -> SemanticValidationResult:
    return always_valid()
