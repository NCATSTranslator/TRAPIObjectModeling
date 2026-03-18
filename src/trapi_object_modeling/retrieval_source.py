from __future__ import annotations

from enum import Enum
from typing import Any, override

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from trapi_object_modeling.shared import Infores
from trapi_object_modeling.utils.object_base import (
    Location,
    SemanticValidationError,
    SemanticValidationErrorList,
    SemanticValidationResult,
    SemanticValidationWarningList,
    TOMBaseObject,
)
from trapi_object_modeling.utils.semantic_validation import (
    extend_location,
    validate_url,
)


class ResourceRoleEnum(str, Enum):
    """The role played by the InformationResource in serving as a source for an Edge.

    Note that a given Edge should have one
    and only one 'primary' source, and may have any number of
    'aggregator' or 'supporting data' sources.  This enumeration
    is found in Biolink Model, but is repeated here for convenience.
    """

    primary_knowledge_source = "primary_knowledge_source"
    """Primary source originating the presented knowledge."""

    aggregator_knowledge_source = "aggregator_knowledge_source"
    """Source which provides the knowledge through aggregation, but did not originate it."""

    supporting_data_source = "supporting_data_source"
    """Source which provides supporting data, but doesn't primarily originate the knowledge."""


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
class RetrievalSource(TOMBaseObject):
    """Provides information about how a particular InformationResource served as a source from which knowledge expressed in an Edge, or data used to generate this knowledge, was retrieved."""

    resource_id: Infores
    """The CURIE for an Information Resource that served as a source of knowledge expressed in an Edge, or a source of data used to generate this knowledge."""

    resource_role: ResourceRoleEnum
    """The role played by the InformationResource in serving as a source for an Edge.

    Note that a given Edge should have one
    and only one 'primary' source, and may have any number of
    'aggregator' or 'supporting data' sources.
    """

    upstream_resource_ids: list[Infores] | None = None
    """An upstream InformationResource from which the resource being described directly retrieved a record of the knowledge expressed in the Edge, or data used to generate this knowledge.

    This is an array because there are cases where a merged Edge
    holds knowledge that was retrieved from multiple sources. e.g.
    an Edge provided by the ARAGORN ARA can expressing knowledge it
    retrieved from both the automat-mychem-info and molepro KPs,
    which both provided it with records of this single fact.
    """

    source_record_urls: list[str] | None = None
    """A URL linking to a specific web page or document provided by the source, that contains a record of the knowledge expressed in the Edge.

    If the knowledge is contained in more than one web page on
    an Information Resource's site, urls MAY be provided for each.
    For example, Therapeutic Targets Database (TTD) has separate web
    pages for 'Imatinib' and its protein target KIT, both of which hold
    the claim that 'the KIT protein is a therapeutic target for Imatinib'.
    """

    @override
    def semantic_validate(
        self, location: Location | None = None, **kwargs: Any
    ) -> SemanticValidationResult:
        warnings, errors = (
            SemanticValidationWarningList(),
            SemanticValidationErrorList(),
        )
        if (
            self.upstream_resource_ids is not None
            and self.resource_id in self.upstream_resource_ids
        ):
            errors.append(
                SemanticValidationError(
                    f"resoure_id {self.resource_id} cannot be present in upstream_resource_ids.",
                    extend_location(location, "upstream_resource_ids"),
                )
            )

        if self.source_record_urls is not None:
            for url in self.source_record_urls:
                new_warn, new_err = validate_url(
                    url, location=extend_location(location, "callback")
                )
                warnings.extend(new_warn)
                errors.extend(new_err)

        return warnings, errors
