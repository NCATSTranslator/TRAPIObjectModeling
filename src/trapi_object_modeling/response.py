from __future__ import annotations

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from trapi_object_modeling.log_entry import LogEntry
from trapi_object_modeling.message import Message
from trapi_object_modeling.workflow_operations import WorkflowOperation


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
class Response:
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

    workflow: list[WorkflowOperation] | None = None
    """List of workflow steps that were executed."""

    schema_version: str | None = None
    """Version label of the TRAPI schema used in this document."""

    biolink_version: str | None = None
    """Version label of the Biolink model used in this document."""
