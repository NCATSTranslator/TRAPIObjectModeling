from __future__ import annotations

from typing import Annotated, Any, override

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass
from stablehash import stablehash

from trapi_object_modeling.log_entry import LogEntry
from trapi_object_modeling.query import Query
from trapi_object_modeling.utils.object_base import (
    Location,
    SemanticValidationResult,
    TOMBaseObject,
)
from trapi_object_modeling.utils.semantic_validation import (
    always_valid,
    extend_location,
    validate_url,
    validation_pipeline,
)


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
class AsyncQuery(Query):
    """The AsyncQuery class is effectively the same as the Query class but it requires a callback property."""

    callback: str
    """Upon completion, this server will send a POST request to the
            callback URL with `Content-Type: application/json` header and
            request body containing a JSON-encoded `Response` object.
            The server MAY POST `Response` objects before work is fully
            complete to provide interim results with a Response.status
            value of 'Running'. If a POST operation to the callback URL
            does not succeed, the server SHOULD retry the POST at least
            once.
    """

    @override
    def hash(self) -> str:
        return stablehash(
            (
                super().hash(),
                self.callback,
            )
        ).hexdigest()

    @override
    def semantic_validate(
        self, location: Location | None = None, **kwargs: Any
    ) -> SemanticValidationResult:
        return validation_pipeline(
            super().semantic_validate(location, **kwargs),
            validate_url(self.callback, location=extend_location(location, "callback")),
        )


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
class AsyncQueryResponse(TOMBaseObject):
    """The AsyncQueryResponse object contains a payload that must be returned from a submitted async_query."""

    status: str | None = None
    """One of a standardized set of short codes: e.g. Accepted, QueryNotTraversable, KPsNotAvailable"""

    description: str | None = None
    """A brief human-readable description of the result of the async_query submission."""

    job_id: str
    """An identifier for the submitted job that can be used with /async_query_status to receive an update on the status of the job."""

    @override
    def semantic_validate(
        self, location: Location | None = None, **kwargs: Any
    ) -> SemanticValidationResult:
        return always_valid()


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
