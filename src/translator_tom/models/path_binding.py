from __future__ import annotations

from typing import ClassVar

from pydantic import ConfigDict

from translator_tom.models.shared import AuxGraphID
from translator_tom.utils.object_base import TOMBaseObject


class PathBinding(TOMBaseObject):
    """A instance of PathBinding is a single binding of an input QueryGraph path (the key to this object) with the AuxiliaryGraph id containing a list of edges in the path.

    The Auxiliary Graph does not convey any order of edges in the path.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")

    id: AuxGraphID
    """The key identifier of a specific auxiliary graph."""
