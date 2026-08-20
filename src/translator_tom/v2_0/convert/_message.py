"""Converter for Message."""

from __future__ import annotations

from typing import Any

from translator_tom.v1_6.models.message import Message as V16Message
from translator_tom.v2_0.convert._util import _build, up_version
from translator_tom.v2_0.models.message import Message


@up_version.register(V16Message)
def _convert_message(obj: V16Message, **kwargs: Any) -> Message:
    """Convert the knowledge/query graphs and results; empty containers → absent."""
    data = obj.to_dict()

    if obj.knowledge_graph is not None:
        data["knowledge_graph"] = up_version(obj.knowledge_graph, **kwargs).to_dict()
    if obj.query_graph is not None:
        data["query_graph"] = up_version(obj.query_graph, **kwargs).to_dict()

    if obj.results:
        data["results"] = [
            up_version(result, **kwargs).to_dict() for result in obj.results
        ]
    else:
        data.pop("results", None)

    if obj.auxiliary_graphs:
        data["auxiliary_graphs"] = {
            aux_id: up_version(graph, **kwargs).to_dict()
            for aux_id, graph in obj.auxiliary_graphs.items()
        }
    else:
        data.pop("auxiliary_graphs", None)

    return _build(Message, data)
