"""Tests for Message.solve_set_interpretation (v2_0 model layer).

Cases mirror SET_INTERPRETATION_EXAMPLES.md. Each message carries a
knowledge_graph (ALL set nodes must exist there), and connectivity comes from
QNodes co-bound within a result, not the edge bindings.
"""

import pytest

from translator_tom import (
    Analysis,
    EdgeBinding,
    KnowledgeGraph,
    Message,
    Node,
    NodeBinding,
    QEdge,
    QNode,
    QueryGraph,
    Result,
)


def _kg(*ids: str) -> KnowledgeGraph:
    return KnowledgeGraph(
        nodes={i: Node(categories=["biolink:NamedThing"], attributes=[]) for i in ids}
    )


def _result(node_bindings: dict[str, str], edge_bindings: dict[str, str]) -> Result:
    return Result(
        node_bindings={q: NodeBinding(ids=[v]) for q, v in node_bindings.items()},
        analyses=[
            Analysis(
                resource_id="infores:test",
                edge_bindings={q: EdgeBinding(ids=[e]) for q, e in edge_bindings.items()},
            )
        ],
    )


def _bindings(message: Message) -> list[dict[str, list[str]]]:
    return [
        {q: sorted(nb.ids) for q, nb in r.node_bindings.items()}
        for r in message.results
    ]


def _edge(subject: str, obj: str) -> QEdge:
    return QEdge(subject=subject, object=obj, predicates=["biolink:related_to"])


class TestBatch:
    def test_passthrough(self):
        qg = QueryGraph(
            nodes={"A": QNode(ids=["A1"]), "B": QNode(categories=["biolink:Gene"])},
            edges={"e0": _edge("A", "B")},
        )
        m = Message(
            query_graph=qg,
            knowledge_graph=_kg("A1", "A2", "B1", "B2", "B3"),
            results=[
                _result({"A": "A1", "B": "B1"}, {"e0": "k1"}),
                _result({"A": "A1", "B": "B2"}, {"e0": "k2"}),
                _result({"A": "A2", "B": "B3"}, {"e0": "k3"}),
            ],
        )
        m.solve_set_interpretation()
        assert len(m.results) == 3
        assert all(len(r.node_bindings["B"].ids) == 1 for r in m.results)


class TestBatchCollate:
    def test_multiple_results_one_per_batch_context(self):
        qg = QueryGraph(
            nodes={
                "A": QNode(ids=["A1"]),
                "B": QNode(categories=["biolink:Gene"], set_interpretation="COLLATE"),
            },
            edges={"e0": _edge("A", "B")},
        )
        m = Message(
            query_graph=qg,
            knowledge_graph=_kg("A1", "A2", "B1", "B2", "B3"),
            results=[
                _result({"A": "A1", "B": "B1"}, {"e0": "k1"}),
                _result({"A": "A1", "B": "B2"}, {"e0": "k2"}),
                _result({"A": "A2", "B": "B3"}, {"e0": "k3"}),
            ],
        )
        m.solve_set_interpretation()
        assert _bindings(m) == [
            {"A": ["A1"], "B": ["B1", "B2"]},
            {"A": ["A2"], "B": ["B3"]},
        ]

    def test_self_edge_candidate_kept(self):
        # A candidate bound to the same knode as its BATCH neighbor (a self-edge) is collated, not dropped.
        qg = QueryGraph(
            nodes={
                "A": QNode(ids=["A1"]),
                "B": QNode(categories=["biolink:Gene"], set_interpretation="COLLATE"),
            },
            edges={"e0": _edge("A", "B")},
        )
        m = Message(
            query_graph=qg,
            knowledge_graph=_kg("A1", "B1"),
            results=[
                _result({"A": "A1", "B": "B1"}, {"e0": "k1"}),
                _result({"A": "A1", "B": "A1"}, {"e0": "k2"}),
            ],
        )
        m.solve_set_interpretation()
        assert _bindings(m) == [{"A": ["A1"], "B": ["A1", "B1"]}]

    def test_single_backing_output_does_not_alias_input(self):
        # The single-backing _materialize fast path must give the output a fresh
        # node_bindings dict, not alias the input result's.
        qg = QueryGraph(
            nodes={
                "A": QNode(ids=["A1"]),
                "B": QNode(categories=["biolink:Gene"], set_interpretation="COLLATE"),
            },
            edges={"e0": _edge("A", "B")},
        )
        r_in = _result({"A": "A1", "B": "B1"}, {"e0": "k1"})
        m = Message(query_graph=qg, knowledge_graph=_kg("A1", "B1"), results=[r_in])
        m.solve_set_interpretation()
        assert len(m.results) == 1
        m.results[0].node_bindings["A"] = NodeBinding(ids=["MUTATED"])
        assert r_in.node_bindings["A"].ids == ["A1"]  # input untouched


class TestBatchAll:
    def test_incomplete_member_edges_drop_group(self):
        qg = QueryGraph(
            nodes={
                "A": QNode(ids=["A1"]),
                "B": QNode(set_interpretation="ALL", ids=["BSET"], member_ids=["B1", "B2"]),
            },
            edges={"e0": _edge("A", "B")},
        )
        m = Message(
            query_graph=qg,
            knowledge_graph=_kg("A1", "A2", "B1", "B2", "BSET"),
            results=[
                _result({"A": "A1", "B": "B1"}, {"e0": "k1"}),
                _result({"A": "A1", "B": "B2"}, {"e0": "k2"}),
                _result({"A": "A2", "B": "B1"}, {"e0": "k3"}),  # A2 lacks B2
            ],
        )
        m.solve_set_interpretation()
        assert _bindings(m) == [{"A": ["A1"], "B": ["BSET"]}]

    def test_missing_member_node_raises(self):
        qg = QueryGraph(
            nodes={
                "A": QNode(ids=["A1"]),
                "B": QNode(set_interpretation="ALL", ids=["BSET"], member_ids=["B1"]),
            },
            edges={"e0": _edge("A", "B")},
        )
        m = Message(
            query_graph=qg,
            knowledge_graph=_kg("A1", "B1"),  # BSET absent
            results=[_result({"A": "A1", "B": "B1"}, {"e0": "k1"})],
        )
        with pytest.raises(ValueError, match="member node"):
            m.solve_set_interpretation()

    def test_no_ids_falls_back_to_batch(self):
        qg = QueryGraph(
            nodes={
                "A": QNode(ids=["A1"]),
                "B": QNode(categories=["biolink:Gene"], set_interpretation="ALL"),
            },
            edges={"e0": _edge("A", "B")},
        )
        m = Message(
            query_graph=qg,
            knowledge_graph=_kg("A1", "B1", "B2"),
            results=[
                _result({"A": "A1", "B": "B1"}, {"e0": "k1"}),
                _result({"A": "A1", "B": "B2"}, {"e0": "k2"}),
            ],
        )
        m.solve_set_interpretation()
        assert len(m.results) == 2  # BATCH behavior


class TestAllAll:
    def _qg(self) -> QueryGraph:
        return QueryGraph(
            nodes={
                "A": QNode(set_interpretation="ALL", ids=["ASET"], member_ids=["A1", "A2"]),
                "B": QNode(set_interpretation="ALL", ids=["BSET"], member_ids=["B1", "B2"]),
            },
            edges={"e0": _edge("A", "B")},
        )

    def test_cross_edges_satisfy(self):
        m = Message(
            query_graph=self._qg(),
            knowledge_graph=_kg("A1", "A2", "B1", "B2", "ASET", "BSET"),
            results=[
                _result({"A": "A1", "B": "B1"}, {"e0": "k1"}),
                _result({"A": "A2", "B": "B2"}, {"e0": "k2"}),
            ],
        )
        m.solve_set_interpretation()
        assert _bindings(m) == [{"A": ["ASET"], "B": ["BSET"]}]

    def test_missing_member_yields_no_results(self):
        m = Message(
            query_graph=self._qg(),
            knowledge_graph=_kg("A1", "A2", "B1", "B2", "ASET", "BSET"),
            results=[_result({"A": "A1", "B": "B1"}, {"e0": "k1"})],  # A2/B2 absent
        )
        m.solve_set_interpretation()
        assert len(m.results) == 0


class TestAllCollate:
    def test_filter_single_result(self):
        qg = QueryGraph(
            nodes={
                "A": QNode(set_interpretation="ALL", ids=["ASET"], member_ids=["A1", "A2"]),
                "B": QNode(categories=["biolink:Gene"], set_interpretation="COLLATE"),
            },
            edges={"e0": _edge("A", "B")},
        )
        m = Message(
            query_graph=qg,
            knowledge_graph=_kg("A1", "A2", "B1", "B2", "B3", "ASET"),
            results=[
                _result({"A": "A1", "B": "B1"}, {"e0": "k1"}),
                _result({"A": "A2", "B": "B1"}, {"e0": "k2"}),
                _result({"A": "A1", "B": "B2"}, {"e0": "k3"}),
                _result({"A": "A2", "B": "B2"}, {"e0": "k4"}),
                _result({"A": "A1", "B": "B3"}, {"e0": "k5"}),  # B3 lacks A2
            ],
        )
        m.solve_set_interpretation()
        assert _bindings(m) == [{"A": ["ASET"], "B": ["B1", "B2"]}]


class TestAllCollateBatchChain:
    def test_two_results_multi_and_single(self):
        qg = QueryGraph(
            nodes={
                "A": QNode(set_interpretation="ALL", ids=["ASET"], member_ids=["A1", "A2"]),
                "B": QNode(categories=["biolink:Gene"], set_interpretation="COLLATE"),
                "C": QNode(ids=["C1"]),
            },
            edges={"e0": _edge("A", "B"), "e1": _edge("B", "C")},
        )
        m = Message(
            query_graph=qg,
            knowledge_graph=_kg("A1", "A2", "B1", "B2", "B3", "B4", "C1", "C2", "ASET"),
            results=[
                _result({"A": "A1", "B": "B1", "C": "C1"}, {"e0": "k1", "e1": "k1b"}),
                _result({"A": "A2", "B": "B1", "C": "C1"}, {"e0": "k2", "e1": "k2b"}),
                _result({"A": "A1", "B": "B2", "C": "C1"}, {"e0": "k3", "e1": "k3b"}),
                _result({"A": "A2", "B": "B2", "C": "C1"}, {"e0": "k4", "e1": "k4b"}),
                _result({"A": "A1", "B": "B4", "C": "C1"}, {"e0": "k5", "e1": "k5b"}),
                _result({"A": "A1", "B": "B3", "C": "C2"}, {"e0": "k6", "e1": "k6b"}),
                _result({"A": "A2", "B": "B3", "C": "C2"}, {"e0": "k7", "e1": "k7b"}),
            ],
        )
        m.solve_set_interpretation()
        assert _bindings(m) == [
            {"A": ["ASET"], "B": ["B1", "B2"], "C": ["C1"]},
            {"A": ["ASET"], "B": ["B3"], "C": ["C2"]},
        ]


class TestCollateCollate:
    def _collate(self) -> QNode:
        return QNode(categories=["biolink:Gene"], set_interpretation="COLLATE")

    def test_disjoint_clusters_split(self):
        qg = QueryGraph(
            nodes={"A": self._collate(), "B": self._collate()},
            edges={"e0": _edge("A", "B")},
        )
        m = Message(
            query_graph=qg,
            knowledge_graph=_kg("a1", "a2", "a3", "a4", "b1", "b2", "b3", "b4"),
            results=[
                _result({"A": "a1", "B": "b1"}, {"e0": "1"}),
                _result({"A": "a1", "B": "b2"}, {"e0": "2"}),
                _result({"A": "a2", "B": "b1"}, {"e0": "3"}),
                _result({"A": "a2", "B": "b2"}, {"e0": "4"}),
                _result({"A": "a3", "B": "b3"}, {"e0": "5"}),
                _result({"A": "a3", "B": "b4"}, {"e0": "6"}),
                _result({"A": "a4", "B": "b3"}, {"e0": "7"}),
                _result({"A": "a4", "B": "b4"}, {"e0": "8"}),
            ],
        )
        m.solve_set_interpretation()
        assert _bindings(m) == [
            {"A": ["a1", "a2"], "B": ["b1", "b2"]},
            {"A": ["a3", "a4"], "B": ["b3", "b4"]},
        ]

    def test_chain_split(self):
        qg = QueryGraph(
            nodes={"A": self._collate(), "B": self._collate(), "C": self._collate()},
            edges={"eab": _edge("A", "B"), "ebc": _edge("B", "C")},
        )
        m = Message(
            query_graph=qg,
            knowledge_graph=_kg("a1", "b1", "b2", "c1", "c2"),
            results=[
                _result({"A": "a1", "B": "b1", "C": "c1"}, {"eab": "1", "ebc": "2"}),
                _result({"A": "a1", "B": "b2", "C": "c2"}, {"eab": "3", "ebc": "4"}),
            ],
        )
        m.solve_set_interpretation()
        assert _bindings(m) == [
            {"A": ["a1"], "B": ["b1"], "C": ["c1"]},
            {"A": ["a1"], "B": ["b2"], "C": ["c2"]},
        ]

    def test_triangle_cyclic(self):
        qg = QueryGraph(
            nodes={"A": self._collate(), "B": self._collate(), "C": self._collate()},
            edges={"eab": _edge("A", "B"), "ebc": _edge("B", "C"), "eac": _edge("A", "C")},
        )
        m = Message(
            query_graph=qg,
            knowledge_graph=_kg("a1", "a2", "b1", "b2", "c1", "c2"),
            results=[
                _result({"A": "a1", "B": "b1", "C": "c1"}, {"eab": "1", "ebc": "2", "eac": "3"}),
                _result({"A": "a2", "B": "b2", "C": "c2"}, {"eab": "4", "ebc": "5", "eac": "6"}),
            ],
        )
        m.solve_set_interpretation()
        assert _bindings(m) == [
            {"A": ["a1"], "B": ["b1"], "C": ["c1"]},
            {"A": ["a2"], "B": ["b2"], "C": ["c2"]},
        ]

    def test_with_batch_neighbor_filters(self):
        # C(BATCH) filters B; only the C1 context survives, then A/B collate.
        qg = QueryGraph(
            nodes={"A": self._collate(), "B": self._collate(), "C": QNode(ids=["c1"])},
            edges={"eab": _edge("A", "B"), "ebc": _edge("B", "C")},
        )
        m = Message(
            query_graph=qg,
            knowledge_graph=_kg("a1", "a2", "b1", "b2", "c1"),
            results=[
                _result({"A": "a1", "B": "b1", "C": "c1"}, {"eab": "1", "ebc": "2"}),
                _result({"A": "a2", "B": "b1", "C": "c1"}, {"eab": "3", "ebc": "4"}),
                _result({"A": "a1", "B": "b2", "C": "c1"}, {"eab": "5", "ebc": "6"}),
                _result({"A": "a2", "B": "b2", "C": "c1"}, {"eab": "7", "ebc": "8"}),
            ],
        )
        m.solve_set_interpretation()
        assert _bindings(m) == [{"A": ["a1", "a2"], "B": ["b1", "b2"], "C": ["c1"]}]

    def test_candidate_cap_raises(self):
        qg = QueryGraph(
            nodes={"A": self._collate(), "B": self._collate()},
            edges={"e0": _edge("A", "B")},
        )
        ids = [f"a{i}" for i in range(3)] + [f"b{i}" for i in range(3)]
        m = Message(
            query_graph=qg,
            knowledge_graph=_kg(*ids),
            results=[
                _result({"A": f"a{i}", "B": f"b{j}"}, {"e0": f"{i}{j}"})
                for i in range(3)
                for j in range(3)
            ],
        )
        with pytest.raises(ValueError, match="max_collate_candidates"):
            m.solve_set_interpretation(max_collate_candidates=4)

    def _two_by_two(self) -> Message:
        # One 2x2 complete-bipartite COLLATE-COLLATE component (4 candidates).
        qg = QueryGraph(
            nodes={"A": self._collate(), "B": self._collate()},
            edges={"e0": _edge("A", "B")},
        )
        return Message(
            query_graph=qg,
            knowledge_graph=_kg("a1", "a2", "b1", "b2"),
            results=[
                _result({"A": f"a{i}", "B": f"b{j}"}, {"e0": f"{i}{j}"})
                for i in (1, 2)
                for j in (1, 2)
            ],
        )

    def test_candidate_cap_zero_rejects_any_adjacent_collate(self):
        with pytest.raises(ValueError, match="max_collate_candidates=0"):
            self._two_by_two().solve_set_interpretation(max_collate_candidates=0)

    def test_candidate_cap_zero_allows_single_collate(self):
        # The cap guards adjacent-COLLATE enumeration only; a lone COLLATE node
        # is not an adjacent component, so cap=0 does not reject it.
        qg = QueryGraph(
            nodes={"A": QNode(ids=["A1"]), "B": self._collate()},
            edges={"e0": _edge("A", "B")},
        )
        m = Message(
            query_graph=qg,
            knowledge_graph=_kg("A1", "B1", "B2"),
            results=[
                _result({"A": "A1", "B": "B1"}, {"e0": "k1"}),
                _result({"A": "A1", "B": "B2"}, {"e0": "k2"}),
            ],
        )
        m.solve_set_interpretation(max_collate_candidates=0)
        assert _bindings(m) == [{"A": ["A1"], "B": ["B1", "B2"]}]

    def test_candidate_cap_negative_disables(self):
        # The 3x3 component raises at a small positive cap; -1 disables it and solves.
        qg = QueryGraph(
            nodes={"A": self._collate(), "B": self._collate()},
            edges={"e0": _edge("A", "B")},
        )
        ids = [f"a{i}" for i in range(3)] + [f"b{i}" for i in range(3)]
        m = Message(
            query_graph=qg,
            knowledge_graph=_kg(*ids),
            results=[
                _result({"A": f"a{i}", "B": f"b{j}"}, {"e0": f"{i}{j}"})
                for i in range(3)
                for j in range(3)
            ],
        )
        m.solve_set_interpretation(max_collate_candidates=-1)
        assert _bindings(m) == [
            {"A": ["a0", "a1", "a2"], "B": ["b0", "b1", "b2"]}
        ]

    def test_independent_components_only_backed_results(self):
        # Two disjoint COLLATE-COLLATE components: only path-backed combos survive
        # (the cross-product must not emit spurious, unbacked results).
        qg = QueryGraph(
            nodes={q: self._collate() for q in ("A", "B", "D", "E")},
            edges={"eab": _edge("A", "B"), "ede": _edge("D", "E")},
        )
        m = Message(
            query_graph=qg,
            knowledge_graph=_kg("a1", "a2", "b1", "b2", "d1", "d2", "e1", "e2"),
            results=[
                _result(
                    {"A": "a1", "B": "b1", "D": "d1", "E": "e1"},
                    {"eab": "ab1", "ede": "de1"},
                ),
                _result(
                    {"A": "a2", "B": "b2", "D": "d2", "E": "e2"},
                    {"eab": "ab2", "ede": "de2"},
                ),
            ],
        )
        m.solve_set_interpretation()
        assert _bindings(m) == [
            {"A": ["a1"], "B": ["b1"], "D": ["d1"], "E": ["e1"]},
            {"A": ["a2"], "B": ["b2"], "D": ["d2"], "E": ["e2"]},
        ]

    def test_clique_count_guard(self):
        qg = QueryGraph(
            nodes={"A": self._collate(), "B": self._collate()},
            edges={"e0": _edge("A", "B")},
        )
        m = Message(
            query_graph=qg,
            knowledge_graph=_kg("a1", "a2", "b1", "b2"),  # two maximal cliques
            results=[
                _result({"A": "a1", "B": "b1"}, {"e0": "1"}),
                _result({"A": "a2", "B": "b2"}, {"e0": "2"}),
            ],
        )
        with pytest.raises(ValueError, match="maximal cliques"):
            m.solve_set_interpretation(max_collate_cliques=1)

    def test_deep_clique_no_recursion_error(self):
        # A clique deeper than the recursion limit must enumerate iteratively (a
        # recursive Bron-Kerbosch blew the stack on large same-qnode candidate sets).
        import sys
        import traceback

        from translator_tom.utils.set_interpretation import _maximal_cliques

        depth = len(traceback.extract_stack())
        n = depth + 200  # clique far deeper than the lowered limit below
        vertices = [("q", f"k{i}") for i in range(n)]
        vset = set(vertices)
        neighbors = {v: vset - {v} for v in vertices}  # all compatible -> one n-clique

        old = sys.getrecursionlimit()
        sys.setrecursionlimit(depth + 40)  # a recursive impl would overflow here
        try:
            cliques = _maximal_cliques(
                vertices, neighbors, max_collate_cliques=-1, required_qnodes={"q"}
            )
        finally:
            sys.setrecursionlimit(old)
        assert cliques == [frozenset(vertices)]


class TestExpandedContract:
    def test_multi_id_binding_raises(self):
        qg = QueryGraph(
            nodes={"A": QNode(ids=["A1"]), "B": QNode(categories=["biolink:Gene"])},
            edges={"e0": _edge("A", "B")},
        )
        m = Message(
            query_graph=qg,
            knowledge_graph=_kg("A1", "B1", "B2"),
            results=[
                Result(
                    node_bindings={
                        "A": NodeBinding(ids=["A1"]),
                        "B": NodeBinding(ids=["B1", "B2"]),  # pre-collated, not a path
                    },
                    analyses=[
                        Analysis(
                            resource_id="infores:test",
                            edge_bindings={"e0": EdgeBinding(ids=["k1"])},
                        )
                    ],
                )
            ],
        )
        with pytest.raises(ValueError, match="one knode per QNode"):
            m.solve_set_interpretation()


class TestMany:
    def _qg(self) -> QueryGraph:
        return QueryGraph(
            nodes={
                "A": QNode(ids=["A1"]),
                "B": QNode(set_interpretation="MANY", ids=["B1", "B2"]),
            },
            edges={"e0": _edge("A", "B")},
        )

    def test_raises_by_default(self):
        m = Message(
            query_graph=self._qg(),
            knowledge_graph=_kg("A1", "B1"),
            results=[_result({"A": "A1", "B": "B1"}, {"e0": "k1"})],
        )
        with pytest.raises(ValueError, match="MANY"):
            m.solve_set_interpretation()

    def test_skip_many_treats_as_batch(self):
        m = Message(
            query_graph=self._qg(),
            knowledge_graph=_kg("A1", "B1", "B2"),
            results=[
                _result({"A": "A1", "B": "B1"}, {"e0": "k1"}),
                _result({"A": "A1", "B": "B2"}, {"e0": "k2"}),
            ],
        )
        m.solve_set_interpretation(skip_many=True)
        assert len(m.results) == 2


class TestNoOp:
    def test_no_query_graph(self):
        m = Message(results=[_result({"A": "A1"}, {"e0": "k1"})])
        m.solve_set_interpretation()
        assert len(m.results) == 1

    def test_no_results(self):
        qg = QueryGraph(nodes={"A": QNode(categories=["biolink:Gene"])})
        m = Message(query_graph=qg)
        m.solve_set_interpretation()
        assert m.results is None


class TestCyclic:
    """Cyclic query graphs with multiple ALL nodes are handled per-edge (locally)."""

    def _all(self, set_id: str, members: list[str]) -> QNode:
        return QNode(set_interpretation="ALL", ids=[set_id], member_ids=members)

    def _triangle_qg(self, a: QNode, b: QNode, c: QNode) -> QueryGraph:
        return QueryGraph(
            nodes={"A": a, "B": b, "C": c},
            edges={
                "eab": _edge("A", "B"),
                "ebc": _edge("B", "C"),
                "eac": _edge("A", "C"),
            },
        )

    def _triangle(self, a: str, b: str, c: str, tag: str) -> Result:
        return _result(
            {"A": a, "B": b, "C": c},
            {"eab": f"{tag}1", "ebc": f"{tag}2", "eac": f"{tag}3"},
        )

    def test_triangle_all_all_closed(self):
        qg = self._triangle_qg(
            self._all("ASET", ["a1", "a2"]),
            self._all("BSET", ["b1", "b2"]),
            self._all("CSET", ["c1", "c2"]),
        )
        m = Message(
            query_graph=qg,
            knowledge_graph=_kg("a1", "a2", "b1", "b2", "c1", "c2", "ASET", "BSET", "CSET"),
            results=[
                self._triangle("a1", "b1", "c1", "x"),
                self._triangle("a2", "b2", "c2", "y"),
            ],
        )
        m.solve_set_interpretation()
        assert _bindings(m) == [{"A": ["ASET"], "B": ["BSET"], "C": ["CSET"]}]

    def test_triangle_missing_member_drops(self):
        qg = self._triangle_qg(
            self._all("ASET", ["a1", "a2"]),
            self._all("BSET", ["b1", "b2"]),
            self._all("CSET", ["c1", "c2"]),
        )
        m = Message(
            query_graph=qg,
            knowledge_graph=_kg("a1", "b1", "c1", "ASET", "BSET", "CSET"),
            results=[self._triangle("a1", "b1", "c1", "x")],  # a2/b2/c2 absent
        )
        m.solve_set_interpretation()
        assert len(m.results) == 0

    def test_triangle_per_edge_cross_path_neighbors(self):
        qg = self._triangle_qg(
            self._all("ASET", ["a1"]),
            self._all("BSET", ["b1", "b2"]),
            self._all("CSET", ["c1", "c2"]),
        )
        m = Message(
            query_graph=qg,
            knowledge_graph=_kg("a1", "b1", "b2", "c1", "c2", "ASET", "BSET", "CSET"),
            results=[
                self._triangle("a1", "b1", "c1", "x"),
                self._triangle("a1", "b2", "c2", "y"),
            ],
        )
        m.solve_set_interpretation()
        assert _bindings(m) == [{"A": ["ASET"], "B": ["BSET"], "C": ["CSET"]}]

    def test_four_cycle_all_all(self):
        qg = QueryGraph(
            nodes={n: self._all(f"{n}SET", [f"{n.lower()}1", f"{n.lower()}2"]) for n in "ABCD"},
            edges={
                "eab": _edge("A", "B"),
                "ebc": _edge("B", "C"),
                "ecd": _edge("C", "D"),
                "eda": _edge("D", "A"),
            },
        )
        kg_ids = [f"{x}{i}" for x in "abcd" for i in (1, 2)] + [f"{n}SET" for n in "ABCD"]
        m = Message(
            query_graph=qg,
            knowledge_graph=_kg(*kg_ids),
            results=[
                _result(
                    {"A": "a1", "B": "b1", "C": "c1", "D": "d1"},
                    {"eab": "1", "ebc": "2", "ecd": "3", "eda": "4"},
                ),
                _result(
                    {"A": "a2", "B": "b2", "C": "c2", "D": "d2"},
                    {"eab": "5", "ebc": "6", "ecd": "7", "eda": "8"},
                ),
            ],
        )
        m.solve_set_interpretation()
        assert _bindings(m) == [
            {"A": ["ASET"], "B": ["BSET"], "C": ["CSET"], "D": ["DSET"]}
        ]
