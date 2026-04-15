from __future__ import annotations

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from trapi_object_modeling.attribute import Attribute
from trapi_object_modeling.shared import EdgeID
from trapi_object_modeling.utils.object_base import TOMBaseObject


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
class EdgeBinding(TOMBaseObject):
    """A instance of EdgeBinding is a single KnowledgeGraph Edge mapping, identified by the corresponding 'id' object key identifier of the Edge within the Knowledge Graph.

    Instances of EdgeBinding may include extra annotation
    (such annotation is not yet fully standardized).
    Edge bindings are captured within a specific reasoner's Analysis
    object because the Edges in the Knowledge Graph that get bound to
    the input Query Graph may differ between reasoners.
    """

    id: EdgeID
    """The key identifier of a specific KnowledgeGraph Edge."""

    attributes: list[Attribute]
    """A list of attributes providing further information about the edge binding.
    This is not intended for capturing edge attributes
    and should only be used for properties that vary from result to
    result.
    """
