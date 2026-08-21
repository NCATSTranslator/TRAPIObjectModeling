"""Transform for Message."""

from __future__ import annotations

from typing import Any

from translator_tom.v1_6.models.message import Message as V16Message
from translator_tom.v2_0.convert._auxiliary_graph import _upgrade_auxiliary_graph
from translator_tom.v2_0.convert._knowledge_graph import _upgrade_knowledge_graph
from translator_tom.v2_0.convert._query_graph import _upgrade_query_graph
from translator_tom.v2_0.convert._result import _upgrade_result
from translator_tom.v2_0.convert._util import register
from translator_tom.v2_0.models.message import Message


@register(V16Message, Message)
def _upgrade_message(data: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Convert the knowledge/query graphs and results; empty containers → absent."""
    data = dict(data)

    knowledge_graph = data.get("knowledge_graph")
    if knowledge_graph is not None:
        data["knowledge_graph"] = _upgrade_knowledge_graph(knowledge_graph, **kwargs)

    query_graph = data.get("query_graph")
    if query_graph is not None:
        data["query_graph"] = _upgrade_query_graph(query_graph, **kwargs)

    results = data.get("results")
    if results:
        data["results"] = [_upgrade_result(result, **kwargs) for result in results]
    else:
        data.pop("results", None)

    auxiliary_graphs = data.get("auxiliary_graphs")
    if auxiliary_graphs:
        data["auxiliary_graphs"] = {
            aux_id: _upgrade_auxiliary_graph(graph, **kwargs)
            for aux_id, graph in auxiliary_graphs.items()
        }
    else:
        data.pop("auxiliary_graphs", None)

    return data
