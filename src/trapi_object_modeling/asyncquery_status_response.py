from __future__ import annotations

from typing import Annotated, Any, override

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from trapi_object_modeling.log_entry import LogEntry
from trapi_object_modeling.utils.object_base import (
    Location,
    SemanticValidationResult,
    TOMBaseObject,
)
from trapi_object_modeling.utils.semantic_validation import (
    always_valid,
    extend_location,
    validate_url,
)


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
class AsyncQueryStatusResponse(TOMBaseObject):
    """The AsyncQueryStatusResponse object contains a payload that describes the current status of a previously submitted async_query."""

    status: str
    """One of a standardized set of short codes: Queued, Running, Completed, Failed"""

    description: str
    """A brief human-readable description of the current state or summary of the problem if the status is Failed."""

    logs: Annotated[list[LogEntry], Field(min_length=1)]
    """A list of LogEntry items, containing errors, warnings, debugging information, etc.

    List items MUST be in chronological order with
    earliest first. The most recent entry should be last. Its timestamp
    will be compared against the current time to see if there is
    still activity.
    """

    response_url: str | None = None
    """Optional URL that can be queried to restrieve the full TRAPI Response."""


    @override
    def semantic_validate(
        self, location: Location | None = None, **kwargs: Any
    ) -> SemanticValidationResult:
        if self.response_url is not None:
            return validate_url(
                self.response_url, location=extend_location(location, "callback")
            )

        # Otherwise, nothing to validate
        return always_valid()
