from __future__ import annotations

from typing_extensions import Self

from translator_tom.utils.config import TRAPI_CONFIG
from translator_tom.utils.object_base import TOMBase
from translator_tom.v1_6._version import SCHEMA_VERSION
from translator_tom.v1_6.models.log_entry import LogEntry
from translator_tom.v1_6.models.message import Message
from translator_tom.v1_6.models.workflow_operations import Operation

__all__ = ["Response"]


class Response(TOMBase):
    """The Response object contains the main payload when a TRAPI query endpoint interprets and responds to the submitted query successfully (i.e., HTTP Status Code 200).

    The message property contains the knowledge of the response
    (query graph, knowledge graph, and results). The status, description, and logs
    properties provide additional details about the response.
    """

    message: Message
    """Contains the knowledge of the response (query graph, knowledge graph, and results)."""

    status: str | None = None
    """One of a standardized set of short codes, e.g. Success, QueryNotTraversable, KPsNotAvailable."""

    description: str | None = None
    """A brief human-readable description of the outcome."""

    logs: list[LogEntry] | None = None
    """A list of LogEntry items, containing errors, warnings, debugging information, etc.

    List items MUST be in chronological order with earliest first.
    """

    workflow: list[Operation] | None = None
    """List of workflow steps that were executed."""

    schema_version: str | None = None
    """Version label of the TRAPI schema used in this document."""

    biolink_version: str | None = None
    """Version label of the Biolink model used in this document."""

    @property
    def workflow_list(self) -> list[Operation]:
        """Get the workflow operations as a guaranteed list, even if they are represented as None."""
        return self.workflow if self.workflow is not None else []

    @property
    def logs_list(self) -> list[LogEntry]:
        """Get the logs as a guaranteed list, even if they are represented as None."""
        return self.logs if self.logs is not None else []

    @classmethod
    def new(cls) -> Self:
        """Return an empty instance, without having to pass required containers."""
        return cls.model_construct(
            message=Message(),
            schema_version=SCHEMA_VERSION,
            biolink_version=TRAPI_CONFIG.biolink_version,
        )
