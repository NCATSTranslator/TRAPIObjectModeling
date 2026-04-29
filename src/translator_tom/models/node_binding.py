from __future__ import annotations

from typing import ClassVar, override

from pydantic import ConfigDict

from translator_tom.models.attribute import Attribute
from translator_tom.models.shared import CURIE
from translator_tom.utils.hash import tomhash
from translator_tom.utils.object_base import TOMBaseObject


class NodeBinding(TOMBaseObject):
    """An instance of NodeBinding is a single KnowledgeGraph Node mapping, identified by the corresponding 'id' object key identifier of the Node within the Knowledge Graph.

    Instances of NodeBinding may include extra annotation in the form of additional properties
    (such annotation is not yet fully standardized).
    Each Node Binding must bind directly to node in the original Query Graph.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")

    id: CURIE
    """The CURIE of a Node within the Knowledge Graph."""

    query_id: CURIE | None = None
    """An optional property to provide the CURIE in the QueryGraph to which this binding applies.

    If the bound QNode does not have an
    an 'id' property or if it is empty, then this query_id MUST be
    null or absent. If the bound QNode has one or more CURIEs
    as an 'id' and this NodeBinding's 'id' refers to a QNode 'id'
    in a manner where the CURIEs are different (typically due to
    the NodeBinding.id being a descendant of a QNode.id), then
    this query_id MUST be provided. In other cases, there is no
    ambiguity, and this query_id SHOULD NOT be provided.
    """

    attributes: list[Attribute]
    """A list of attributes providing further information about the node binding.
    This is not intended for capturing node attributes
    and should only be used for properties that vary from result to
    result.
    """

    @override
    def hash(self) -> str:
        return tomhash(
            (self.id, self.query_id, frozenset(a.hash() for a in self.attributes))
        )
