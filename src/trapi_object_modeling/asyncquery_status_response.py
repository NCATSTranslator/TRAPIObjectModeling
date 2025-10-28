from __future__ import annotations

from typing import Annotated

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from trapi_object_modeling.log_entry import LogEntry


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
class AsyncQueryStatusResponse:
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
