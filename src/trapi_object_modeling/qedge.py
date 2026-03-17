from __future__ import annotations

from typing import Annotated

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from trapi_object_modeling.attribute_constraint import AttributeConstraint
from trapi_object_modeling.qualifier_constraint import QualifierConstraint
from trapi_object_modeling.shared import (
    BiolinkPredicate,
    KnowledgeTypeEnum,
    QNodeID,
)
from trapi_object_modeling.utils.object_base import TOMBaseObject


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
class QEdge(TOMBaseObject):
    """An edge in the QueryGraph used as a filter pattern specification in a query.

    If the optional predicate property is not specified,
    it is assumed to be a wildcard match to the target knowledge space.
    If specified, the ontological inheritance hierarchy associated with
    the term provided is assumed, such that edge bindings returned may be
    an exact match to the given QEdge predicate term,
    or to a term that is a descendant of the QEdge predicate term.
    """

    knowledge_types: KnowledgeTypeEnum | None = None
    """Indicates the type of knowledge that the client wants from the server between the subject and object.

    If the value is 'lookup', then the client wants direct lookup information from
    knowledge sources. If the value is 'inferred', then the client
    wants the server to get creative and connect the subject and
    object in more speculative and non-direct-lookup ways. If this
    property is absent or null, it MUST be assumed to mean
    'lookup'. This feature is currently experimental and may be
    further extended in the future.
    """

    predicates: Annotated[list[BiolinkPredicate] | None, Field(min_length=1)] = None
    """These should be Biolink Model predicates and are allowed to be of type 'abstract' or 'mixin' (only in QGraphs!).

    Use of 'deprecated' predicates should be avoided."""

    subject: QNodeID
    """Corresponds to the map key identifier of the subject concept node anchoring the query filter pattern for the query relationship edge."""

    object: QNodeID
    """Corresponds to the map key identifier of the object concept node anchoring the query filter pattern for the query relationship edge."""

    attribute_constraints: list[AttributeConstraint] | None = None
    """A list of attribute constraints applied to a query edge. If there are multiple items, they must all be true (equivalent to AND)."""

    qualifier_constraints: list[QualifierConstraint] | None = None
    """A list of QualifierConstraints that provide nuance to the QEdge.

    If multiple QualifierConstraints are provided, there is an OR
    relationship between them. If the QEdge has multiple
    predicates or if the QNodes that correspond to the subject or
    object of this QEdge have multiple categories or multiple
    curies, then qualifier_constraints MUST NOT be specified
    because these complex use cases are not supported at this time.
    """
