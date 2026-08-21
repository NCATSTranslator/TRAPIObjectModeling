"""Parity tests for the analysis `*DictUtil` classes."""

from __future__ import annotations

from translator_tom.v1_6.model_dicts.analysis import (
    AnalysisDictUtil,
    BaseAnalysisDictUtil,
    PathfinderAnalysisDictUtil,
)
from translator_tom.v1_6.models.analysis import (
    Analysis,
    BaseAnalysis,
    PathfinderAnalysis,
)
from translator_tom.v1_6.models.attribute import Attribute
from translator_tom.v1_6.models.edge_binding import EdgeBinding
from translator_tom.v1_6.models.path_binding import PathBinding


def _eb(edge_id: str) -> EdgeBinding:
    return EdgeBinding(id=edge_id, attributes=[])


class TestBaseAnalysis:
    def test_list_accessors(self):
        a = BaseAnalysis(
            resource_id="infores:x",
            support_graphs=["a0"],
            attributes=[Attribute(attribute_type_id="biolink:x", value=1)],
        )
        assert BaseAnalysisDictUtil.support_graphs_list(a.to_dict()) == ["a0"]
        assert len(BaseAnalysisDictUtil.attributes_list(a.to_dict())) == 1

    def test_hash_parity(self):
        a = BaseAnalysis(
            resource_id="infores:x",
            score=0.5,
            support_graphs=["a0", "a1"],
            scoring_method="method",
        )
        assert BaseAnalysisDictUtil.hash(a.to_dict()) == a.hash()


class TestAnalysisHashParity:
    def test_minimal(self):
        a = Analysis(resource_id="infores:x", edge_bindings={})
        assert AnalysisDictUtil.hash(a.to_dict()) == a.hash()

    def test_with_bindings(self):
        a = Analysis(
            resource_id="infores:x",
            score=0.9,
            edge_bindings={"e0": [_eb("kg0"), _eb("kg1")]},
        )
        assert AnalysisDictUtil.hash(a.to_dict()) == a.hash()


class TestAnalysisUpdate:
    def test_merges_edge_bindings(self):
        a = Analysis(
            resource_id="infores:x",
            support_graphs=["a0"],
            edge_bindings={"e0": [_eb("kg0")]},
        )
        other = Analysis(
            resource_id="infores:x",
            support_graphs=["a1"],
            edge_bindings={"e0": [_eb("kg1")], "e1": [_eb("kg2")]},
        )
        a_dict = a.to_dict()
        a.update(other)
        AnalysisDictUtil.update(a_dict, other.to_dict())
        # Bindings are merged via a set in the model (order not meaningful); the
        # analysis hash folds them into frozensets, so parity is order-independent.
        assert AnalysisDictUtil.hash(a_dict) == a.hash()
        assert set(a_dict["support_graphs"]) == set(a.support_graphs or [])


class TestPathfinderAnalysis:
    def test_hash_parity(self):
        a = PathfinderAnalysis(
            resource_id="infores:x",
            path_bindings={"p0": [PathBinding(id="a0"), PathBinding(id="a1")]},
        )
        assert PathfinderAnalysisDictUtil.hash(a.to_dict()) == a.hash()

    def test_update_parity(self):
        a = PathfinderAnalysis(
            resource_id="infores:x", path_bindings={"p0": [PathBinding(id="a0")]}
        )
        other = PathfinderAnalysis(
            resource_id="infores:x",
            path_bindings={"p0": [PathBinding(id="a1")], "p1": [PathBinding(id="a2")]},
        )
        a_dict = a.to_dict()
        a.update(other)
        PathfinderAnalysisDictUtil.update(a_dict, other.to_dict())
        assert PathfinderAnalysisDictUtil.hash(a_dict) == a.hash()


class TestAnalysisUpdateBranches:
    """Dedup edge cases: intra-key overlap (existing wins), deepcopy isolation, base merge."""

    def test_intra_key_overlap_existing_wins(self):
        a = Analysis(resource_id="infores:x", edge_bindings={"e0": [_eb("kg0")]})
        other = Analysis(
            resource_id="infores:x", edge_bindings={"e0": [_eb("kg0"), _eb("kg1")]}
        )
        a_dict = a.to_dict()
        AnalysisDictUtil.update(a_dict, other.to_dict())
        assert {b["id"] for b in a_dict["edge_bindings"]["e0"]} == {"kg0", "kg1"}

    def test_incoming_bindings_are_deepcopied(self):
        # a dropped copy.deepcopy would let a later mutation of `other` leak into the result
        a = Analysis(resource_id="infores:x", edge_bindings={"e0": [_eb("kg0")]})
        other = Analysis(resource_id="infores:x", edge_bindings={"e1": [_eb("kg1")]})
        a_dict, other_dict = a.to_dict(), other.to_dict()
        AnalysisDictUtil.update(a_dict, other_dict)
        other_dict["edge_bindings"]["e1"][0]["id"] = "MUTATED"
        assert a_dict["edge_bindings"]["e1"][0]["id"] == "kg1"

    def test_update_base_merges_attributes(self):
        a = Analysis(
            resource_id="infores:x",
            edge_bindings={},
            attributes=[Attribute(attribute_type_id="biolink:x", value=1)],
        )
        other = Analysis(
            resource_id="infores:x",
            edge_bindings={},
            attributes=[Attribute(attribute_type_id="biolink:y", value=2)],
        )
        a_dict = a.to_dict()
        a.update(other)
        AnalysisDictUtil.update(a_dict, other.to_dict())
        assert AnalysisDictUtil.hash(a_dict) == a.hash()
        assert len(a_dict.get("attributes", [])) == 2
