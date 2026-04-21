from __future__ import annotations

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from translator_tom.models.shared import AuxGraphID
from translator_tom.utils.object_base import TOMBaseObject


@dataclass(kw_only=True, config=ConfigDict(extra="allow"), eq=False)
class PathBinding(TOMBaseObject):
    """A instance of PathBinding is a single binding of an input QueryGraph path (the key to this object) with the AuxiliaryGraph id containing a list of edges in the path.

    The Auxiliary Graph does not convey any order of edges in the path.
    """

    id: AuxGraphID
    """The key identifier of a specific auxiliary graph."""
