"""Tests for translator_tom.models.result."""

import pytest
from pydantic import ValidationError

from translator_tom import (
    Analysis,
    Attribute,
    EdgeBinding,
    NodeBinding,
    PathBinding,
    PathfinderAnalysis,
    Result,
)


def _nb(node_id: str = "A:1") -> NodeBinding:
    return NodeBinding(id=node_id, attributes=[])


def _eb(edge_id: str = "e1") -> EdgeBinding:
    return EdgeBinding(id=edge_id, attributes=[])


def _analysis(resource_id: str = "infores:test", edge_id: str = "e1") -> Analysis:
    return Analysis(
        resource_id=resource_id,
        edge_bindings={"e0": [_eb(edge_id)]},
    )


def _result(node_id: str = "A:1", edge_id: str = "e1") -> Result:
    return Result(
        node_bindings={"n0": [_nb(node_id)]},
        analyses=[_analysis(edge_id=edge_id)],
    )


class TestResultBasics:
    def test_required_fields(self):
        r = _result()
        assert "n0" in r.node_bindings
        assert len(r.analyses) == 1

    def test_node_binding_min_length_per_qnode(self):
        with pytest.raises(ValidationError):
            Result(node_bindings={"n0": []}, analyses=[])


class TestResultHash:
    def test_only_depends_on_node_bindings(self):
        # Two results with identical node_bindings but different analyses
        # share a hash.
        a = Result(
            node_bindings={"n0": [_nb("A:1")]},
            analyses=[_analysis(edge_id="e1")],
        )
        b = Result(
            node_bindings={"n0": [_nb("A:1")]},
            analyses=[_analysis(edge_id="e2")],
        )
        assert a.hash() == b.hash()

    def test_changes_with_node_bindings(self):
        a = Result(node_bindings={"n0": [_nb("A:1")]}, analyses=[])
        b = Result(node_bindings={"n0": [_nb("A:9")]}, analyses=[])
        assert a.hash() != b.hash()


class TestResultNormalize:
    def test_remaps_edge_binding_ids(self):
        r = _result(edge_id="old_edge")
        r.normalize({"old_edge": "new_edge"})
        assert r.analyses[0].edge_bindings["e0"][0].id == "new_edge"  # type: ignore[union-attr]

    def test_unmapped_edges_unchanged(self):
        r = _result(edge_id="other_edge")
        r.normalize({"old_edge": "new_edge"})
        assert r.analyses[0].edge_bindings["e0"][0].id == "other_edge"  # type: ignore[union-attr]

    def test_skips_pathfinder_analysis(self):
        r = Result(
            node_bindings={"n0": [_nb()]},
            analyses=[
                PathfinderAnalysis(
                    resource_id="infores:p",
                    path_bindings={"p0": [PathBinding(id="aux1")]},
                )
            ],
        )
        # No edge_bindings to remap; should not raise.
        r.normalize({"x": "y"})


class TestResultNormalizeList:
    def test_normalizes_each_result(self):
        results = [_result(edge_id="old_a"), _result(edge_id="old_b")]
        Result.normalize_list(results, {"old_a": "new_a", "old_b": "new_b"})
        assert results[0].analyses[0].edge_bindings["e0"][0].id == "new_a"  # type: ignore[union-attr]
        assert results[1].analyses[0].edge_bindings["e0"][0].id == "new_b"  # type: ignore[union-attr]


class TestResultUpdate:
    def test_returns_early_when_other_has_no_analyses(self):
        a = _result()
        b = Result(node_bindings={"n0": [_nb()]}, analyses=[])
        a.update(b)
        assert len(a.analyses) == 1

    def test_assigns_when_self_has_no_analyses(self):
        a = Result(node_bindings={"n0": [_nb()]}, analyses=[])
        b = _result()
        a.update(b)
        assert len(a.analyses) == 1

    def test_appends_new_analysis(self):
        a = _result(edge_id="e1")
        b = Result(
            node_bindings={"n0": [_nb()]},
            analyses=[_analysis(resource_id="infores:other", edge_id="e2")],
        )
        a.update(b)
        assert len(a.analyses) == 2

    def test_merges_existing_analysis_by_hash(self):
        # Two analyses with same resource_id and same edge_bindings keys
        # share the same hash.
        a = _result(edge_id="e1")
        b = _result(edge_id="e1")
        a.update(b)
        assert len(a.analyses) == 1


class TestResultMergeResults:
    def test_dedupes_by_hash(self):
        a = _result(node_id="A:1")
        b = _result(node_id="A:1")
        results = [a, b]
        merged = Result.merge_results(results)
        assert len(merged) == 1

    def test_keeps_distinct_results(self):
        a = _result(node_id="A:1")
        b = _result(node_id="A:2")
        merged = Result.merge_results([a, b])
        assert len(merged) == 2

    def test_merges_in_place(self):
        results = [_result(node_id="A:1")]
        original_id = id(results)
        Result.merge_results(results, [_result(node_id="A:1")])
        assert id(results) == original_id
        assert len(results) == 1

    def test_new_arg_handles_none(self):
        results = [_result(node_id="A:1")]
        Result.merge_results(results)  # new defaults to []
        assert len(results) == 1


class TestMergeAnalysesByResourceId:
    def test_collapses_same_resource_id(self):
        a = _analysis(resource_id="infores:foo", edge_id="e1")
        b = _analysis(resource_id="infores:foo", edge_id="e2")
        r = Result(
            node_bindings={"n0": [_nb()]},
            analyses=[a, b],
        )
        r.merge_analyses_by_resource_id()
        assert len(r.analyses) == 1

    def test_keeps_distinct_resource_ids(self):
        r = Result(
            node_bindings={"n0": [_nb()]},
            analyses=[
                _analysis(resource_id="infores:a"),
                _analysis(resource_id="infores:b"),
            ],
        )
        r.merge_analyses_by_resource_id()
        assert len(r.analyses) == 2

    def test_keeps_different_types_separate(self):
        # Same resource_id but different analysis types are kept distinct
        # because the merge key includes type(analysis).
        r = Result(
            node_bindings={"n0": [_nb()]},
            analyses=[
                _analysis(resource_id="infores:a"),
                PathfinderAnalysis(
                    resource_id="infores:a",
                    path_bindings={"p0": [PathBinding(id="aux1")]},
                ),
            ],
        )
        r.merge_analyses_by_resource_id()
        assert len(r.analyses) == 2
