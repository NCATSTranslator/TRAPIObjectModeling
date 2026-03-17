from __future__ import annotations

from typing import Annotated

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from trapi_object_modeling.meta_attribute import MetaAttribute
from trapi_object_modeling.meta_qualifier import MetaQualifier
from trapi_object_modeling.shared import (
    BiolinkEntity,
    BiolinkPredicate,
    KnowledgeTypeEnum,
)
from trapi_object_modeling.utils.object_base import TOMBaseObject


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class MetaEdge(TOMBaseObject):
    """Edge in a meta knowledge map describing relationship between a subject Biolink class and an object Biolink class."""

    subject: BiolinkEntity
    """Subject node category of this relationship edge."""

    predicate: BiolinkPredicate
    """Biolink relationship between the subject and object categories."""

    object: BiolinkEntity
    """Object node category of this relationship edge."""

    knowledge_types: Annotated[list[KnowledgeTypeEnum] | None, Field(min_length=1)] = (
        None
    )
    """A list of knowledge_types that are supported by the service.

    If the knowledge_types is null, this means that only 'lookup'
    is supported. Currently allowed values are 'lookup' or 'inferred'.
    """

    attributes: list[MetaAttribute] | None = None
    """Edge attributes provided by this TRAPI web service."""

    qualifiers: list[MetaQualifier] | None = None
    """Qualifiers that are possible to be found on this edge type."""

    association: BiolinkEntity | None = None
    """The Biolink association type (entity) that this edge represents.

    Associations are classes in Biolink
    that represent a relationship between two entities.
    For example, the association 'gene interacts with gene'
    is represented by the Biolink class,
    'biolink:GeneToGeneAssociation'.  If association
    is filled out, then the testing harness can
    help validate that the qualifiers are being used
    correctly.
    """
