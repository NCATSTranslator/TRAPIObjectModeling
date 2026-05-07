from __future__ import annotations

from typing import Any

from translator_tom.models.log_entry import LogEntry
from translator_tom.validation._util import (
    Location,
    SemanticValidationResult,
    always_valid,
    semantic_validate,
)


@semantic_validate.register(LogEntry)
def _validate_log_entry(
    obj: LogEntry,
    location: Location | None = None,
    **_: Any,
) -> SemanticValidationResult:
    return always_valid()
