from __future__ import annotations

from typing import Annotated

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from trapi_object_modeling.attribute import Attribute
from trapi_object_modeling.shared import BiolinkEntity
from trapi_object_modeling.utils.object_base import TOMBaseObject


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class Node(TOMBaseObject):
    """A node in the KnowledgeGraph which represents some biomedical concept.

    Nodes are identified by the keys in the KnowledgeGraph Node mapping.
    """

    name: str | None = None
    """Formal name of the entity."""

    categories: Annotated[list[BiolinkEntity], Field(min_length=1)]
    """These should be Biolink Model categories and are NOT allowed to be of type 'abstract' or 'mixin'.

    Returning 'deprecated' categories should also be avoided.
    """

    attributes: list[Attribute]
    """A list of attributes describing the node."""

    is_set: bool | None = None
    """Indicates that the node represents a set of entities.

    If this property is missing or null, it is assumed to be false.
    """
