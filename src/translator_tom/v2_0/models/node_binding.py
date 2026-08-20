from __future__ import annotations

from typing import Annotated

from pydantic import Field
from typing_extensions import override

from translator_tom.utils.object_base import TOMBase
from translator_tom.utils.shared import CURIE

__all__ = ["NodeBinding"]


class NodeBinding(TOMBase):
    """A NodeBinding object defines all relevant KnowledgeGraph Node mappings, identified by the corresponding object key identifier(s) of the Node(s) within the Knowledge Graph.

    Instances of NodeBinding may
    include extra annotation in the form of additional properties.
    (such annotation is not yet fully standardized). Each Node
    Binding must bind directly to node in the original Query Graph.
    """

    ids: Annotated[list[CURIE], Field(min_length=1)]
    """The CURIEs of one or more Nodes within the Knowledge Graph."""

    @override
    def _hash_repr(self) -> object:
        return frozenset(self.ids)
