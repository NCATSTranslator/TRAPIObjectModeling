from __future__ import annotations

from typing import Any, override

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from trapi_object_modeling.log_entry import LogEntry
from trapi_object_modeling.message import Message
from trapi_object_modeling.utils.config import TRAPI_CONFIG
from trapi_object_modeling.utils.object_base import (
    Location,
    SemanticValidationResult,
    SemanticValidationWarning,
    TOMBaseObject,
)
from trapi_object_modeling.utils.semantic_validation import (
    extend_location,
    get_list_locations,
    validate_many,
    validation_pipeline,
)
from trapi_object_modeling.workflow_operations import WorkflowOperation


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
class Response(TOMBaseObject):
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

    logs: list[LogEntry] = Field(default_factory=list)
    """A list of LogEntry items, containing errors, warnings, debugging information, etc.

    List items MUST be in chronological order with earliest first.
    """

    workflow: list[WorkflowOperation] | None = None
    """List of workflow steps that were executed."""

    schema_version: str | None = None
    """Version label of the TRAPI schema used in this document."""

    biolink_version: str | None = None
    """Version label of the Biolink model used in this document."""

    @property
    def workflow_list(self) -> list[WorkflowOperation]:
        """Get the workflow operations as a guaranteed list, even if they are represented as None."""
        return self.workflow if self.workflow is not None else []

    @override
    def semantic_validate(
        self, location: Location | None = None, **kwargs: Any
    ) -> SemanticValidationResult:
        warnings, errors = validation_pipeline(
            self.message.semantic_validate(location),
            validate_many(
                *self.logs,
                locations=get_list_locations(
                    self.logs, extend_location(location, "logs")
                ),
            ),
            validate_many(
                *self.workflow_list,
                locations=get_list_locations(
                    self.workflow_list, extend_location(location, "workflow")
                ),
                qgraph=self.message.query_graph,
            ),
        )
        if self.schema_version != TRAPI_CONFIG.schema_version:
            warnings.append(
                SemanticValidationWarning(
                    f"Response schema_version `{self.schema_version}` does not match TOM schema_version `{TRAPI_CONFIG.schema_version}`.",
                    extend_location(location, "schema_version"),
                ),
            )
        if self.biolink_version != TRAPI_CONFIG.biolink_version:
            warnings.append(
                SemanticValidationWarning(
                    f"Response biolink_version `{self.biolink_version}` does not match configured TOM biolink_version `{TRAPI_CONFIG.biolink_version}`."
                )
            )

        return warnings, errors
