from __future__ import annotations

from typing import Any

from trapi_object_modeling.models.log_entry import LogEntry
from trapi_object_modeling.validation._util import (
    Location,
    SemanticValidationResult,
    always_valid,
    semantic_validate,
)


@semantic_validate.register(LogEntry)
def _validate_log_entry(  # pyright: ignore[reportUnusedFunction]
    obj: LogEntry,  # pyright: ignore[reportUnusedParameter]
    location: Location | None = None,  # pyright: ignore[reportUnusedParameter]
    **kwargs: Any,  # pyright: ignore[reportUnusedParameter]
) -> SemanticValidationResult:
    return always_valid()
