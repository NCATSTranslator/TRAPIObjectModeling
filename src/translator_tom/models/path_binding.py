from __future__ import annotations

from typing import Annotated

from pydantic import Field
from typing_extensions import override

from translator_tom.models.shared import AuxGraphID
from translator_tom.utils.object_base import TOMBase

__all__ = ["PathBinding"]


class PathBinding(TOMBase):
    """A PathBinding object binds a single QueryGraph path (the key to this object) to one or more relevant AuxiliaryGraph ids containing a list of edges in the path.

    The AuxiliaryGraph does not convey any
    order of edges in the path.
    """

    ids: Annotated[list[AuxGraphID], Field(min_length=1)]
    """The key identifiers of specific auxiliary graphs."""

    @override
    def _hash_repr(self) -> object:
        return frozenset(self.ids)
