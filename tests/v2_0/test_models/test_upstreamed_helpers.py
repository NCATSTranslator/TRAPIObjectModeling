"""Tests for the TRAPI navigation/transform helpers upstreamed from xCRG (v2_0)."""

from translator_tom import (
    Analysis,
    EdgeBinding,
    NodeBinding,
    QEdge,
    QEdgeConstraints,
    QNode,
    Qualifier,
    QueryGraph,
    Result,
)


def _qedge_with_qualifiers() -> QEdge:
    return QEdge(
        subject="n0",
        object="n1",
        constraints=QEdgeConstraints(
            qualifiers=[
                {
                    "biolink:object_aspect_qualifier": "activity",
                    "biolink:object_direction_qualifier": "increased",
                }
            ]
        ),
    )


def _result() -> Result:
    return Result(
        node_bindings={"n1": NodeBinding(ids=["X:1", "X:2"])},
        analyses=[
            Analysis(
                resource_id="infores:a",
                edge_bindings={"e0": EdgeBinding(ids=["kg:1"])},
            ),
            Analysis(
                resource_id="infores:b",
                edge_bindings={
                    "e0": EdgeBinding(ids=["kg:1"]),
                    "e1": EdgeBinding(ids=["kg:9"]),
                },
            ),
        ],
    )


class TestGetUnpinned:
    def test_by_qedge_returns_unpinned_endpoint(self):
        qg = QueryGraph(
            nodes={"n0": QNode(ids=["CHEBI:1"]), "n1": QNode(categories=["biolink:Gene"])},
            edges={"e0": QEdge(subject="n0", object="n1")},
        )
        assert [qid for qid, _ in qg.get_unpinned("e0")] == ["n1"]

    def test_without_qedge_returns_all_unpinned(self):
        qg = QueryGraph(
            nodes={"n0": QNode(ids=["CHEBI:1"]), "n1": QNode(), "n2": QNode()},
            edges={"e0": QEdge(subject="n0", object="n1")},
        )
        assert sorted(qid for qid, _ in qg.get_unpinned()) == ["n1", "n2"]

    def test_returns_the_qnode_object(self):
        n1 = QNode(categories=["biolink:Gene"])
        qg = QueryGraph(
            nodes={"n0": QNode(ids=["CHEBI:1"]), "n1": n1},
            edges={"e0": QEdge(subject="n0", object="n1")},
        )
        assert qg.get_unpinned("e0") == [("n1", n1)]


class TestGetQualifierValue:
    def test_present(self):
        assert (
            _qedge_with_qualifiers().get_qualifier_value(
                "biolink:object_aspect_qualifier"
            )
            == "activity"
        )

    def test_absent(self):
        assert (
            _qedge_with_qualifiers().get_qualifier_value(
                "biolink:subject_aspect_qualifier"
            )
            is None
        )

    def test_no_constraints(self):
        assert (
            QEdge(subject="n0", object="n1").get_qualifier_value(
                "biolink:object_aspect_qualifier"
            )
            is None
        )


class TestSetFromQedge:
    def test_builds_qualifiers(self):
        quals = Qualifier.set_from_qedge(_qedge_with_qualifiers())
        assert {(q.qualifier_type_id, q.qualifier_value) for q in quals} == {
            ("biolink:object_aspect_qualifier", "activity"),
            ("biolink:object_direction_qualifier", "increased"),
        }

    def test_no_constraints_returns_empty(self):
        assert Qualifier.set_from_qedge(QEdge(subject="n0", object="n1")) == []


class TestResultHelpers:
    def test_edge_bindings_deduped_across_analyses(self):
        bindings = _result().edge_bindings("e0")
        assert len(bindings) == 1
        assert bindings[0].ids == ["kg:1"]

    def test_edge_bindings_missing_qedge(self):
        assert _result().edge_bindings("nope") == []

    def test_bound_kedges(self):
        assert _result().bound_kedges() == {"e0", "e1"}
