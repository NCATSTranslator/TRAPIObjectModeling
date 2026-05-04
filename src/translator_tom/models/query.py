from __future__ import annotations

from typing import Self

from translator_tom.models.log_entry import LogLevel
from translator_tom.models.message import Message
from translator_tom.models.workflow_operations import Operation
from translator_tom.utils.object_base import TOMBaseObject


class Query(TOMBaseObject):
    """The Query class is used to package a user request for information.

    A Query object consists of a required Message object with optional
    additional properties. Additional properties are intended to convey
    implementation-specific or query-independent parameters. For example,
    an additional property specifying a log level could allow a user to
    override the default log level in order to receive more fine-grained
    log information when debugging an issue.
    """

    message: Message
    """The query Message is a serialization of the user request.

    Content of the Message object depends on the intended TRAPI operation.
    For example, the fill operation requires a non-empty query_graph field
    as part of the Message, whereas other operations, e.g. overlay,
    require non-empty results and knowledge_graph fields.
    """

    log_level: LogLevel | None = None
    """The least critical level of logs to return."""

    workflow: list[Operation] | None = None
    """List of workflow steps to be executed."""

    submitter: str | None = None
    """Any string for self-identifying the submitter of a query.

    The purpose of this optional field is to aid in the tracking of
    the source of queries for development and issue resolution.
    """

    bypass_cache: bool = False
    """Set to true in order to request that the agent obtain
    fresh information from its sources in all cases where
    it has a viable choice between requesting fresh information
    in real time and using cached information.

    The agent receiving this flag MUST also include it in TRAPI sent to
    downstream sources (e.g., ARS -> ARAs -> KPs).
    """

    @property
    def workflow_list(self) -> list[Operation]:
        """Get the workflow operations as a guaranteed list, even if they are represented as None."""
        return self.workflow if self.workflow is not None else []

    @classmethod
    def new(cls) -> Self:
        """Return an empty instance, without having to pass required containers."""
        return cls(message=Message())
