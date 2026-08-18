from __future__ import annotations

from typing import Annotated

from pydantic import Field
from typing_extensions import override

from translator_tom.models.shared import EdgeID
from translator_tom.utils.object_base import TOMBase

__all__ = ["EdgeBinding"]


class EdgeBinding(TOMBase):
    """An EdgeBinding object defines all relevant KnowledgeGraph Edge mappings, identified by the corresponding 'id' object key identifier of the Edge within the knowledge graph.

    Instances of EdgeBinding may include
    extra annotation (such annotation is not yet fully standardized).
    EdgeBindings are captured within a specific reasoner's Analysis
    object because the Edges in the KnowledgeGraph that get bound to
    the input QueryGraph may differ between reasoners.
    """

    ids: Annotated[list[EdgeID], Field(min_length=1)]
    """The key identifiers of specific KnowledgeGraph Edges."""

    @override
    def _hash_repr(self) -> object:
        return frozenset(self.ids)
