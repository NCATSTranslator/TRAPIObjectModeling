from __future__ import annotations

from translator_tom.utils.dict_util_base import DictUtil, TOMBaseDict
from translator_tom.utils.shared import AuxGraphID
from translator_tom.v1_6.models.path_binding import PathBinding

__all__ = ["PathBindingDict", "PathBindingDictUtil"]


class PathBindingDict(TOMBaseDict):
    id: AuxGraphID


class PathBindingDictUtil(DictUtil[PathBindingDict]):
    """Registration-only util for `PathBindingDict`."""

    _model = PathBinding
