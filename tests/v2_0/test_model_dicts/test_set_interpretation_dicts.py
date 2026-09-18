"""Parity tests for MessageDictUtil.solve_set_interpretation (v2_0 dict layer)."""

import pytest

from translator_tom.v2_0.model_dicts.message import MessageDict, MessageDictUtil
from translator_tom.v2_0.models.message import Message


def _kg(*ids: str) -> dict:
    return {"nodes": {i: {"categories": ["biolink:NamedThing"], "attributes": []} for i in ids}}


def _result(node_bindings: dict[str, str], edge_bindings: dict[str, str]) -> dict:
    return {
        "node_bindings": {q: {"ids": [v]} for q, v in node_bindings.items()},
        "analyses": [
            {
                "resource_id": "infores:test",
                "edge_bindings": {q: {"ids": [e]} for q, e in edge_bindings.items()},
            }
        ],
    }


def _bindings(message: MessageDict) -> list[dict[str, list[str]]]:
    return [
        {q: sorted(nb["ids"]) for q, nb in r["node_bindings"].items()}
        for r in message["results"]
    ]


def test_batch_collate_multiple_results():
    m: MessageDict = {
        "query_graph": {
            "nodes": {
                "A": {"ids": ["A1"]},
                "B": {"categories": ["biolink:Gene"], "set_interpretation": "COLLATE"},
            },
            "edges": {"e0": {"subject": "A", "object": "B"}},
        },
        "knowledge_graph": _kg("A1", "A2", "B1", "B2", "B3"),
        "results": [
            _result({"A": "A1", "B": "B1"}, {"e0": "k1"}),
            _result({"A": "A1", "B": "B2"}, {"e0": "k2"}),
            _result({"A": "A2", "B": "B3"}, {"e0": "k3"}),
        ],
    }
    MessageDictUtil.solve_set_interpretation(m)
    assert _bindings(m) == [{"A": ["A1"], "B": ["B1", "B2"]}, {"A": ["A2"], "B": ["B3"]}]


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


def test_collate_collate_disjoint_split():
    def collate() -> dict:
        return {"categories": ["biolink:Gene"], "set_interpretation": "COLLATE"}

    m: MessageDict = {
        "query_graph": {
            "nodes": {"A": collate(), "B": collate()},
            "edges": {"e0": {"subject": "A", "object": "B"}},
        },
        "knowledge_graph": _kg("a1", "a2", "a3", "a4", "b1", "b2", "b3", "b4"),
        "results": [
            _result({"A": "a1", "B": "b1"}, {"e0": "1"}),
            _result({"A": "a1", "B": "b2"}, {"e0": "2"}),
            _result({"A": "a2", "B": "b1"}, {"e0": "3"}),
            _result({"A": "a2", "B": "b2"}, {"e0": "4"}),
            _result({"A": "a3", "B": "b3"}, {"e0": "5"}),
            _result({"A": "a3", "B": "b4"}, {"e0": "6"}),
            _result({"A": "a4", "B": "b3"}, {"e0": "7"}),
            _result({"A": "a4", "B": "b4"}, {"e0": "8"}),
        ],
    }
    MessageDictUtil.solve_set_interpretation(m)
    assert _bindings(m) == [
        {"A": ["a1", "a2"], "B": ["b1", "b2"]},
        {"A": ["a3", "a4"], "B": ["b3", "b4"]},
    ]


def test_collate_collate_cap_raises():
    def collate() -> dict:
        return {"categories": ["biolink:Gene"], "set_interpretation": "COLLATE"}

    m: MessageDict = {
        "query_graph": {
            "nodes": {"A": collate(), "B": collate()},
            "edges": {"e0": {"subject": "A", "object": "B"}},
        },
        "knowledge_graph": _kg("a0", "a1", "a2", "b0", "b1", "b2"),
        "results": [
            _result({"A": f"a{i}", "B": f"b{j}"}, {"e0": f"{i}{j}"})
            for i in range(3)
            for j in range(3)
        ],
    }
    with pytest.raises(ValueError, match="max_collate_candidates"):
        MessageDictUtil.solve_set_interpretation(m, max_collate_candidates=4)


def test_model_dict_parity_collate_collate():
    def collate() -> dict:
        return {"categories": ["biolink:Gene"], "set_interpretation": "COLLATE"}

    qg = {
        "nodes": {"A": collate(), "B": collate()},
        "edges": {"e0": {"subject": "A", "object": "B"}},
    }
    kg = _kg("a1", "a2", "a3", "a4", "b1", "b2", "b3", "b4")
    results = [
        _result({"A": "a1", "B": "b1"}, {"e0": "1"}),
        _result({"A": "a1", "B": "b2"}, {"e0": "2"}),
        _result({"A": "a2", "B": "b1"}, {"e0": "3"}),
        _result({"A": "a2", "B": "b2"}, {"e0": "4"}),
        _result({"A": "a3", "B": "b3"}, {"e0": "5"}),
        _result({"A": "a4", "B": "b4"}, {"e0": "6"}),
    ]
    model = Message.from_dict({"query_graph": qg, "knowledge_graph": kg, "results": results})
    model.solve_set_interpretation()

    as_dict: MessageDict = {"query_graph": qg, "knowledge_graph": kg, "results": results}
    MessageDictUtil.solve_set_interpretation(as_dict)

    assert Message.from_dict(as_dict).hash() == model.hash()


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


def test_model_dict_parity_chain():
    """The dict solver matches the model solver on the ALL–COLLATE–BATCH chain."""
    qg = {
        "nodes": {
            "A": {"set_interpretation": "ALL", "ids": ["ASET"], "member_ids": ["A1", "A2"]},
            "B": {"categories": ["biolink:Gene"], "set_interpretation": "COLLATE"},
            "C": {"ids": ["C1"]},
        },
        "edges": {"e0": {"subject": "A", "object": "B"}, "e1": {"subject": "B", "object": "C"}},
    }
    kg = _kg("A1", "A2", "B1", "B2", "B3", "B4", "C1", "C2", "ASET")
    results = [
        _result({"A": "A1", "B": "B1", "C": "C1"}, {"e0": "k1", "e1": "k1b"}),
        _result({"A": "A2", "B": "B1", "C": "C1"}, {"e0": "k2", "e1": "k2b"}),
        _result({"A": "A1", "B": "B2", "C": "C1"}, {"e0": "k3", "e1": "k3b"}),
        _result({"A": "A2", "B": "B2", "C": "C1"}, {"e0": "k4", "e1": "k4b"}),
        _result({"A": "A1", "B": "B4", "C": "C1"}, {"e0": "k5", "e1": "k5b"}),
        _result({"A": "A1", "B": "B3", "C": "C2"}, {"e0": "k6", "e1": "k6b"}),
        _result({"A": "A2", "B": "B3", "C": "C2"}, {"e0": "k7", "e1": "k7b"}),
    ]

    model = Message.from_dict({"query_graph": qg, "knowledge_graph": kg, "results": results})
    model.solve_set_interpretation()

    as_dict: MessageDict = {"query_graph": qg, "knowledge_graph": kg, "results": results}
    MessageDictUtil.solve_set_interpretation(as_dict)

    assert Message.from_dict(as_dict).hash() == model.hash()


def test_independent_components_only_backed_results():
    def collate() -> dict:
        return {"categories": ["biolink:Gene"], "set_interpretation": "COLLATE"}

    m: MessageDict = {
        "query_graph": {
            "nodes": {q: collate() for q in ("A", "B", "D", "E")},
            "edges": {
                "eab": {"subject": "A", "object": "B"},
                "ede": {"subject": "D", "object": "E"},
            },
        },
        "knowledge_graph": _kg("a1", "a2", "b1", "b2", "d1", "d2", "e1", "e2"),
        "results": [
            _result({"A": "a1", "B": "b1", "D": "d1", "E": "e1"}, {"eab": "ab1", "ede": "de1"}),
            _result({"A": "a2", "B": "b2", "D": "d2", "E": "e2"}, {"eab": "ab2", "ede": "de2"}),
        ],
    }
    MessageDictUtil.solve_set_interpretation(m)
    assert _bindings(m) == [
        {"A": ["a1"], "B": ["b1"], "D": ["d1"], "E": ["e1"]},
        {"A": ["a2"], "B": ["b2"], "D": ["d2"], "E": ["e2"]},
    ]


def test_multi_id_binding_raises():
    m: MessageDict = {
        "query_graph": {
            "nodes": {"A": {"ids": ["A1"]}, "B": {"categories": ["biolink:Gene"]}},
            "edges": {"e0": {"subject": "A", "object": "B"}},
        },
        "knowledge_graph": _kg("A1", "B1", "B2"),
        "results": [
            {
                "node_bindings": {"A": {"ids": ["A1"]}, "B": {"ids": ["B1", "B2"]}},
                "analyses": [
                    {"resource_id": "infores:test", "edge_bindings": {"e0": {"ids": ["k1"]}}}
                ],
            }
        ],
    }
    with pytest.raises(ValueError, match="one knode per QNode"):
        MessageDictUtil.solve_set_interpretation(m)
