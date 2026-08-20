"""Tests for translator_tom.v2_0.models.result."""

import pytest
from pydantic import ValidationError

from translator_tom import (
    Analysis,
    EdgeBinding,
    NodeBinding,
    PathBinding,
    Result,
)


def _nb(*node_ids: str) -> NodeBinding:
    return NodeBinding(ids=list(node_ids) or ["A:1"])


def _eb(*edge_ids: str) -> EdgeBinding:
    return EdgeBinding(ids=list(edge_ids) or ["e1"])


def _pb(*aux_ids: str) -> PathBinding:
    return PathBinding(ids=list(aux_ids) or ["aux1"])


def _analysis(resource_id: str = "infores:test", edge_id: str = "e1") -> Analysis:
    return Analysis(
        resource_id=resource_id,
        edge_bindings={"e0": _eb(edge_id)},
    )


def _result(node_id: str = "A:1", edge_id: str = "e1") -> Result:
    return Result(
        node_bindings={"n0": _nb(node_id)},
        analyses=[_analysis(edge_id=edge_id)],
    )


class TestResultBasics:
    def test_required_fields(self):
        r = _result()
        assert "n0" in r.node_bindings
        assert r.analyses is not None
        assert len(r.analyses) == 1

    def test_analyses_optional(self):
        r = Result(node_bindings={"n0": _nb()})
        assert r.analyses is None
        assert r.analyses_list == []

    def test_node_bindings_min_length(self):
        with pytest.raises(ValidationError):
            Result(node_bindings={})

    def test_analyses_min_length_when_present(self):
        # analyses is optional, but an empty list is invalid (omit instead).
        with pytest.raises(ValidationError):
            Result(node_bindings={"n0": _nb()}, analyses=[])


class TestResultHash:
    def test_only_depends_on_node_bindings(self):
        # Two results with identical node_bindings but different analyses
        # share a hash.
        a = Result(
            node_bindings={"n0": _nb("A:1")},
            analyses=[_analysis(edge_id="e1")],
        )
        b = Result(
            node_bindings={"n0": _nb("A:1")},
            analyses=[_analysis(edge_id="e2")],
        )
        assert a.hash() == b.hash()

    def test_changes_with_node_bindings(self):
        a = Result(node_bindings={"n0": _nb("A:1")})
        b = Result(node_bindings={"n0": _nb("A:9")})
        assert a.hash() != b.hash()


class TestResultNormalize:
    def test_remaps_edge_binding_ids(self):
        r = _result(edge_id="old_edge")
        r.normalize({"old_edge": "new_edge"})
        assert r.analyses[0].edge_bindings["e0"].ids == ["new_edge"]  # type: ignore[index, union-attr]

    def test_unmapped_edges_unchanged(self):
        r = _result(edge_id="other_edge")
        r.normalize({"old_edge": "new_edge"})
        assert r.analyses[0].edge_bindings["e0"].ids == ["other_edge"]  # type: ignore[index, union-attr]

    def test_ignores_path_only_analysis(self):
        r = Result(
            node_bindings={"n0": _nb()},
            analyses=[
                Analysis(
                    resource_id="infores:p",
                    path_bindings={"p0": _pb("aux1")},
                )
            ],
        )
        # No edge_bindings to remap; should not raise.
        r.normalize({"x": "y"})


class TestResultNormalizeList:
    def test_normalizes_each_result(self):
        results = [_result(edge_id="old_a"), _result(edge_id="old_b")]
        Result.normalize_list(results, {"old_a": "new_a", "old_b": "new_b"})
        assert results[0].analyses[0].edge_bindings["e0"].ids == ["new_a"]  # type: ignore[index, union-attr]
        assert results[1].analyses[0].edge_bindings["e0"].ids == ["new_b"]  # type: ignore[index, union-attr]


class TestResultUpdate:
    def test_returns_early_when_other_has_no_analyses(self):
        a = _result()
        b = Result(node_bindings={"n0": _nb()})
        a.update(b)
        assert a.analyses is not None
        assert len(a.analyses) == 1

    def test_assigns_when_self_has_no_analyses(self):
        a = Result(node_bindings={"n0": _nb()})
        b = _result()
        a.update(b)
        assert a.analyses is not None
        assert len(a.analyses) == 1

    def test_appends_new_analysis(self):
        a = _result(edge_id="e1")
        b = Result(
            node_bindings={"n0": _nb()},
            analyses=[_analysis(resource_id="infores:other", edge_id="e2")],
        )
        a.update(b)
        assert a.analyses is not None
        assert len(a.analyses) == 2

    def test_merges_existing_analysis_by_hash(self):
        # Two analyses with same resource_id and same edge_bindings keys
        # share the same hash.
        a = _result(edge_id="e1")
        b = _result(edge_id="e1")
        a.update(b)
        assert a.analyses is not None
        assert len(a.analyses) == 1

    def test_dedupes_internal_duplicate_analyses_in_other(self):
        # `other` carries two equal-hash analyses absent from self; they must collapse
        # to one on merge (each append registers in by_hash), not both re-append.
        a = _result(edge_id="e1")
        b = Result(
            node_bindings={"n0": _nb()},
            analyses=[
                _analysis(resource_id="infores:other", edge_id="e2"),
                _analysis(resource_id="infores:other", edge_id="e2"),
            ],
        )
        a.update(b)
        assert len(a.analyses) == 2  # self's original + one deduped from other


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
            node_bindings={"n0": _nb()},
            analyses=[a, b],
        )
        r.merge_analyses_by_resource_id()
        assert r.analyses is not None
        assert len(r.analyses) == 1

    def test_keeps_distinct_resource_ids(self):
        r = Result(
            node_bindings={"n0": _nb()},
            analyses=[
                _analysis(resource_id="infores:a"),
                _analysis(resource_id="infores:b"),
            ],
        )
        r.merge_analyses_by_resource_id()
        assert r.analyses is not None
        assert len(r.analyses) == 2

    def test_merges_edge_and_path_bindings_same_resource(self):
        # A lookup-style (edge_bindings) and pathfinder-style (path_bindings)
        # analysis with the same resource_id merge into a single analysis
        # carrying both.
        r = Result(
            node_bindings={"n0": _nb()},
            analyses=[
                Analysis(resource_id="infores:a", edge_bindings={"e0": _eb("k1")}),
                Analysis(resource_id="infores:a", path_bindings={"p0": _pb("aux1")}),
            ],
        )
        r.merge_analyses_by_resource_id()
        assert r.analyses is not None
        assert len(r.analyses) == 1
        assert r.analyses[0].edge_bindings is not None
        assert r.analyses[0].path_bindings is not None
