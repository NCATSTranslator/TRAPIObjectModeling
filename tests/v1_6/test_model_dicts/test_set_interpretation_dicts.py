"""Parity tests for MessageDictUtil.solve_set_interpretation (v1_6 dict layer)."""

import pytest

from translator_tom.v1_6.model_dicts.message import MessageDict, MessageDictUtil
from translator_tom.v1_6.models.message import Message


def _kg(*ids: str) -> dict:
    return {
        "nodes": {i: {"categories": ["biolink:NamedThing"], "attributes": []} for i in ids},
        "edges": {},
    }


def _result(node_bindings: dict[str, str], edge_bindings: dict[str, str]) -> dict:
    return {
        "node_bindings": {
            q: [{"id": v, "attributes": []}] for q, v in node_bindings.items()
        },
        "analyses": [
            {
                "resource_id": "infores:test",
                "edge_bindings": {
                    q: [{"id": e, "attributes": []}] for q, e in edge_bindings.items()
                },
            }
        ],
    }


def _bindings(message: MessageDict) -> list[dict[str, list[str]]]:
    return [
        {q: sorted(b["id"] for b in bs) for q, bs in r["node_bindings"].items()}
        for r in message["results"]
    ]


def test_all_binds_set_node_and_drops_incomplete():
    m: MessageDict = {
        "query_graph": {
            "nodes": {
                "A": {"ids": ["A1"]},
                "B": {"set_interpretation": "ALL", "ids": ["BSET"], "member_ids": ["B1", "B2"]},
            },
            "edges": {"e0": {"subject": "A", "object": "B"}},
        },
        "knowledge_graph": _kg("A1", "A2", "B1", "B2", "BSET"),
        "results": [
            _result({"A": "A1", "B": "B1"}, {"e0": "k1"}),
            _result({"A": "A1", "B": "B2"}, {"e0": "k2"}),
            _result({"A": "A2", "B": "B1"}, {"e0": "k3"}),
        ],
    }
    MessageDictUtil.solve_set_interpretation(m)
    assert _bindings(m) == [{"A": ["A1"], "B": ["BSET"]}]


def test_missing_member_node_raises():
    m: MessageDict = {
        "query_graph": {
            "nodes": {
                "A": {"ids": ["A1"]},
                "B": {"set_interpretation": "ALL", "ids": ["BSET"], "member_ids": ["B1"]},
            },
            "edges": {"e0": {"subject": "A", "object": "B"}},
        },
        "knowledge_graph": _kg("A1", "B1"),
        "results": [_result({"A": "A1", "B": "B1"}, {"e0": "k1"})],
    }
    with pytest.raises(ValueError, match="member node"):
        MessageDictUtil.solve_set_interpretation(m)


def test_many_raises_and_skip():
    def build() -> MessageDict:
        return {
            "query_graph": {
                "nodes": {
                    "A": {"ids": ["A1"]},
                    "B": {"set_interpretation": "MANY", "ids": ["B1", "B2"]},
                },
                "edges": {"e0": {"subject": "A", "object": "B"}},
            },
            "knowledge_graph": _kg("A1", "B1", "B2"),
            "results": [
                _result({"A": "A1", "B": "B1"}, {"e0": "k1"}),
                _result({"A": "A1", "B": "B2"}, {"e0": "k2"}),
            ],
        }

    with pytest.raises(ValueError, match="MANY"):
        MessageDictUtil.solve_set_interpretation(build())
    m = build()
    MessageDictUtil.solve_set_interpretation(m, skip_many=True)
    assert len(m["results"]) == 2


def test_model_dict_parity():
    qg = {
        "nodes": {
            "A": {"set_interpretation": "ALL", "ids": ["ASET"], "member_ids": ["A1", "A2"]},
            "B": {"set_interpretation": "ALL", "ids": ["BSET"], "member_ids": ["B1", "B2"]},
        },
        "edges": {"e0": {"subject": "A", "object": "B"}},
    }
    kg = _kg("A1", "A2", "B1", "B2", "ASET", "BSET")
    results = [
        _result({"A": "A1", "B": "B1"}, {"e0": "k1"}),
        _result({"A": "A2", "B": "B2"}, {"e0": "k2"}),
    ]

    model = Message.from_dict({"query_graph": qg, "knowledge_graph": kg, "results": results})
    model.solve_set_interpretation()

    as_dict: MessageDict = {"query_graph": qg, "knowledge_graph": kg, "results": results}
    MessageDictUtil.solve_set_interpretation(as_dict)

    assert Message.from_dict(as_dict).hash() == model.hash()
