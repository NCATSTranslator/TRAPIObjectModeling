from __future__ import annotations

from typing import override

from stablehash import stablehash

from translator_tom.models.attribute import Attribute
from translator_tom.models.shared import EdgeID
from translator_tom.utils.object_base import TOMBaseObject


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

    @override
    def hash(self) -> str:
        return stablehash((self.id, frozenset(self.attributes))).hexdigest()
