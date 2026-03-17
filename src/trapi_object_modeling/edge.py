from __future__ import annotations

from typing import Annotated

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from trapi_object_modeling.attribute import Attribute
from trapi_object_modeling.qualifier import Qualifier
from trapi_object_modeling.retrieval_source import RetrievalSource
from trapi_object_modeling.shared import CURIE, BiolinkPredicate
from trapi_object_modeling.utils.object_base import TOMBaseObject


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class Edge(TOMBaseObject):
    """A specification of the semantic relationship linking two concepts that are expressed as nodes in the knowledge "thought" graph resulting from a query upon the underlying knowledge source."""

    predicate: BiolinkPredicate
    """The type of relationship between the subject and object for the statement expressed in an Edge.

    These should be Biolink Model predicate terms and are NOT allowed

    to be of type 'abstract' or 'mixin'. Returning 'deprecated'
    predicate terms should also be avoided."""

    subject: CURIE
    """Corresponds to the map key CURIE of the subject concept node of this relationship edge."""

    object: CURIE
    """Corresponds to the map key CURIE of the object concept node of this relationship edge."""

    attributes: list[Attribute] | None = None
    """A list of additional attributes for this edge."""

    qualifiers: list[Qualifier] | None = None
    """A set of Qualifiers that act together to add nuance or detail to the statement expressed in an Edge."""

    sources: Annotated[list[RetrievalSource], Field(min_length=1)]
