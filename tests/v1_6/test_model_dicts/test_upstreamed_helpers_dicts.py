"""Parity tests for the xCRG-upstreamed helpers on the v1_6 `*DictUtil` classes."""

from translator_tom.v1_6.model_dicts.qualifier import QualifierDictUtil
from translator_tom.v1_6.model_dicts.query_graph import QEdgeDictUtil, QueryGraphDictUtil
from translator_tom.v1_6.model_dicts.result import ResultDictUtil
from translator_tom.v1_6.models.analysis import Analysis
from translator_tom.v1_6.models.edge_binding import EdgeBinding
from translator_tom.v1_6.models.node_binding import NodeBinding
from translator_tom.v1_6.models.qualifier import Qualifier, QualifierConstraint
from translator_tom.v1_6.models.query_graph import QEdge, QNode, QueryGraph
from translator_tom.v1_6.models.result import Result


def _qgraph() -> QueryGraph:
    return QueryGraph(
        nodes={
            "n0": QNode(ids=["CHEBI:1"]),
            "n1": QNode(categories=["biolink:Gene"]),
            "n2": QNode(),
        },
        edges={
            "e0": QEdge(
                subject="n0",
                object="n1",
                qualifier_constraints=[
                    QualifierConstraint(
                        qualifier_set=[
                            Qualifier(
                                qualifier_type_id="biolink:object_aspect_qualifier",
                                qualifier_value="activity",
                            )
                        ]
                    )
                ],
            )
        },
    )


def _result() -> Result:
    return Result(
        node_bindings={
            "n1": [
                NodeBinding(id="X:1", attributes=[]),
                NodeBinding(id="X:2", attributes=[]),
            ]
        },
        analyses=[
            Analysis(
                resource_id="infores:a",
                edge_bindings={"e0": [EdgeBinding(id="kg:1", attributes=[])]},
            ),
            Analysis(
                resource_id="infores:b",
                edge_bindings={
                    "e0": [EdgeBinding(id="kg:1", attributes=[])],
                    "e1": [EdgeBinding(id="kg:9", attributes=[])],
                },
            ),
        ],
    )


class TestQueryGraphDictUtil:
    def test_get_unpinned_by_qedge(self):
        qgd = _qgraph().to_dict()
        assert [qid for qid, _ in QueryGraphDictUtil.get_unpinned(qgd, "e0")] == ["n1"]

    def test_get_unpinned_all(self):
        qgd = _qgraph().to_dict()
        assert sorted(qid for qid, _ in QueryGraphDictUtil.get_unpinned(qgd)) == [
            "n1",
            "n2",
        ]

    def test_get_unpinned_parity(self):
        qg = _qgraph()
        model = [(qid, qnode.to_dict()) for qid, qnode in qg.get_unpinned("e0")]
        assert QueryGraphDictUtil.get_unpinned(qg.to_dict(), "e0") == model


class TestQEdgeDictUtil:
    def test_get_qualifier_value_present(self):
        ed = _qgraph().to_dict()["edges"]["e0"]
        assert (
            QEdgeDictUtil.get_qualifier_value(ed, "biolink:object_aspect_qualifier")
            == "activity"
        )

    def test_get_qualifier_value_absent(self):
        ed = _qgraph().to_dict()["edges"]["e0"]
        assert (
            QEdgeDictUtil.get_qualifier_value(ed, "biolink:subject_aspect_qualifier")
            is None
        )


class TestQualifierDictUtil:
    def test_set_from_qedge_parity(self):
        qe = _qgraph().edges["e0"]
        model = [q.to_dict() for q in Qualifier.set_from_qedge(qe)]
        assert QualifierDictUtil.set_from_qedge(qe.to_dict()) == model


class TestResultDictUtil:
    def test_edge_bindings_deduped_parity(self):
        r = _result()
        model = [b.to_dict() for b in r.edge_bindings("e0")]
        dict_bindings = ResultDictUtil.edge_bindings(r.to_dict(), "e0")
        assert len(dict_bindings) == 1
        assert dict_bindings == model

    def test_bound_kedges(self):
        assert ResultDictUtil.bound_kedges(_result().to_dict()) == {"e0", "e1"}
