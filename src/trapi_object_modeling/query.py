from __future__ import annotations

from typing import Any, override

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from trapi_object_modeling.log_entry import LogLevelValue
from trapi_object_modeling.message import Message
from trapi_object_modeling.utils.object_base import (
    Location,
    SemanticValidationResult,
    TOMBaseObject,
)
from trapi_object_modeling.utils.semantic_validation import (
    extend_location,
    get_list_locations,
    validate_many,
    validation_pipeline,
)
from trapi_object_modeling.workflow_operations import WorkflowOperation

# FIX: need to somehow warn or guard against this
# PROBLEM: hashing being enabled means that these classes can be stored in sets and used as keys and such
# This becomes a problem if the instance is mutated, because then its hash changes


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
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

    log_level: LogLevelValue | None = None
    """The least critical level of logs to return."""

    workflow: list[WorkflowOperation] | None = None
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
    def workflow_list(self) -> list[WorkflowOperation]:
        """Get the workflow operations as a guaranteed list, even if they are represented as None."""
        return self.workflow if self.workflow is not None else []

    @override
    def semantic_validate(
        self, location: Location | None = None, **kwargs: Any
    ) -> SemanticValidationResult:
        return validation_pipeline(
            self.message.semantic_validate(),
            validate_many(
                *self.workflow_list,
                locations=get_list_locations(
                    self.workflow_list, extend_location(location, "workflow")
                ),
            ),
        )
