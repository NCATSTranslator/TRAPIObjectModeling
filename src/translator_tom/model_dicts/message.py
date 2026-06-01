from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from translator_tom.model_dicts.auxiliary_graph import AuxiliaryGraphDict
from translator_tom.model_dicts.knowledge_graph import KnowledgeGraphDict
from translator_tom.model_dicts.query_graph import (
    PathfinderQueryGraphDict,
    QueryGraphDict,
)
from translator_tom.model_dicts.result import ResultDict
from translator_tom.models.shared import AuxGraphID

__all__ = ["MessageDict"]


class MessageDict(TypedDict):
    results: NotRequired[list[ResultDict] | None]
    query_graph: NotRequired[QueryGraphDict | PathfinderQueryGraphDict | None]
    knowledge_graph: NotRequired[KnowledgeGraphDict | None]
    auxiliary_graphs: NotRequired[dict[AuxGraphID, AuxiliaryGraphDict] | None]
