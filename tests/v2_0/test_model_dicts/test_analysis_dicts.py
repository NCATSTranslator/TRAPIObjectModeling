"""Parity tests for `AnalysisDictUtil`.

In TRAPI 2.0 the Base/Pathfinder Analysis split is gone: there is one
`Analysis`/`AnalysisDict`. `edge_bindings`/`path_bindings` map each Q-key to a
single binding carrying an `ids` list, and `update` merges per key by unioning
those ids.
"""

from __future__ import annotations

from translator_tom.v2_0.model_dicts.analysis import AnalysisDictUtil
from translator_tom.v2_0.models.analysis import Analysis
from translator_tom.v2_0.models.attribute import Attribute
from translator_tom.v2_0.models.edge_binding import EdgeBinding
from translator_tom.v2_0.models.path_binding import PathBinding


def _eb(*edge_ids: str) -> EdgeBinding:
    return EdgeBinding(ids=list(edge_ids) or ["e1"])


def _pb(*aux_ids: str) -> PathBinding:
    return PathBinding(ids=list(aux_ids) or ["aux1"])


class TestAnalysisAccessors:
    def test_list_accessors(self):
        a = Analysis(
            resource_id="infores:x",
            support_graphs=["a0"],
            attributes=[Attribute(attribute_type_id="biolink:x", value=1)],
        )
        assert AnalysisDictUtil.support_graphs_list(a.to_dict()) == ["a0"]
        assert len(AnalysisDictUtil.attributes_list(a.to_dict())) == 1

    def test_scalar_hash_parity(self):
        a = Analysis(
            resource_id="infores:x",
            score=0.5,
            support_graphs=["a0", "a1"],
            scoring_method="method",
        )
        assert AnalysisDictUtil.hash(a.to_dict()) == a.hash()


class TestAnalysisHashParity:
    def test_minimal(self):
        a = Analysis(resource_id="infores:x")
        assert AnalysisDictUtil.hash(a.to_dict()) == a.hash()

    def test_with_edge_bindings(self):
        a = Analysis(
            resource_id="infores:x",
            score=0.9,
            edge_bindings={"e0": _eb("kg0", "kg1")},
        )
        assert AnalysisDictUtil.hash(a.to_dict()) == a.hash()

    def test_with_path_bindings(self):
        a = Analysis(
            resource_id="infores:x",
            path_bindings={"p0": _pb("a0", "a1")},
        )
        assert AnalysisDictUtil.hash(a.to_dict()) == a.hash()


class TestAnalysisUpdate:
    def test_merges_edge_bindings(self):
        a = Analysis(
            resource_id="infores:x",
            support_graphs=["a0"],
            edge_bindings={"e0": _eb("kg0")},
        )
        other = Analysis(
            resource_id="infores:x",
            support_graphs=["a1"],
            edge_bindings={"e0": _eb("kg1"), "e1": _eb("kg2")},
        )
        a_dict = a.to_dict()
        a.update(other)
        AnalysisDictUtil.update(a_dict, other.to_dict())
        # Binding ids are unioned per key and support_graphs via a set; the analysis
        # hash folds both into frozensets, so parity is order-independent.
        assert AnalysisDictUtil.hash(a_dict) == a.hash()
        assert set(a_dict["support_graphs"]) == set(a.support_graphs or [])

    def test_merges_path_bindings(self):
        a = Analysis(resource_id="infores:x", path_bindings={"p0": _pb("a0")})
        other = Analysis(
            resource_id="infores:x",
            path_bindings={"p0": _pb("a1"), "p1": _pb("a2")},
        )
        a_dict = a.to_dict()
        a.update(other)
        AnalysisDictUtil.update(a_dict, other.to_dict())
        assert AnalysisDictUtil.hash(a_dict) == a.hash()


class TestAnalysisUpdateBranches:
    """Dedup edge cases: intra-key id union, deepcopy isolation, base merge."""

    def test_intra_key_ids_unioned(self):
        a = Analysis(resource_id="infores:x", edge_bindings={"e0": _eb("kg0")})
        other = Analysis(
            resource_id="infores:x", edge_bindings={"e0": _eb("kg0", "kg1")}
        )
        a_dict = a.to_dict()
        AnalysisDictUtil.update(a_dict, other.to_dict())
        assert set(a_dict["edge_bindings"]["e0"]["ids"]) == {"kg0", "kg1"}

    def test_incoming_bindings_are_deepcopied(self):
        # a dropped copy.deepcopy would let a later mutation of `other` leak into the result
        a = Analysis(resource_id="infores:x", edge_bindings={"e0": _eb("kg0")})
        other = Analysis(resource_id="infores:x", edge_bindings={"e1": _eb("kg1")})
        a_dict, other_dict = a.to_dict(), other.to_dict()
        AnalysisDictUtil.update(a_dict, other_dict)
        other_dict["edge_bindings"]["e1"]["ids"][0] = "MUTATED"
        assert a_dict["edge_bindings"]["e1"]["ids"][0] == "kg1"

    def test_update_base_merges_attributes(self):
        a = Analysis(
            resource_id="infores:x",
            attributes=[Attribute(attribute_type_id="biolink:x", value=1)],
        )
        other = Analysis(
            resource_id="infores:x",
            attributes=[Attribute(attribute_type_id="biolink:y", value=2)],
        )
        a_dict = a.to_dict()
        a.update(other)
        AnalysisDictUtil.update(a_dict, other.to_dict())
        assert AnalysisDictUtil.hash(a_dict) == a.hash()
        assert len(a_dict.get("attributes", [])) == 2
