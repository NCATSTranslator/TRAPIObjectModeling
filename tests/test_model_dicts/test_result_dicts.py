"""Parity tests for `ResultDictUtil`."""

from __future__ import annotations

from typing import Any

from translator_tom.model_dicts.analysis import (
    AnalysisDictUtil,
    PathfinderAnalysisDictUtil,
)
from translator_tom.model_dicts.result import ResultDict, ResultDictUtil
from translator_tom.models.analysis import Analysis
from translator_tom.models.attribute import Attribute
from translator_tom.models.edge_binding import EdgeBinding
from translator_tom.models.node_binding import NodeBinding
from translator_tom.models.result import Result


def _eb(edge_id: str) -> EdgeBinding:
    return EdgeBinding(id=edge_id, attributes=[])


def _result(qnode: str, node_id: str, analyses: list[Analysis]) -> Result:
    return Result(
        node_bindings={qnode: [NodeBinding(id=node_id, attributes=[])]},
        analyses=analyses,
    )


def _dict_analysis_hash(analysis: dict[str, Any]) -> str:
    if "path_bindings" in analysis:
        return PathfinderAnalysisDictUtil.hash(analysis)  # type: ignore[arg-type]
    return AnalysisDictUtil.hash(analysis)  # type: ignore[arg-type]


def _dict_analysis_hashes(result: ResultDict) -> list[str]:
    return sorted(_dict_analysis_hash(a) for a in result["analyses"])


def _model_analysis_hashes(result: Result) -> list[str]:
    return sorted(a.hash() for a in result.analyses)


class TestHashParity:
    def test_parity(self):
        r = _result(
            "n0", "CHEBI:1", [Analysis(resource_id="infores:x", edge_bindings={})]
        )
        assert ResultDictUtil.hash(r.to_dict()) == r.hash()

    def test_hash_ignores_analyses(self):
        # Result.hash keys only on node_bindings.
        a = _result("n0", "CHEBI:1", [Analysis(resource_id="infores:x", edge_bindings={})])
        b = _result("n0", "CHEBI:1", [])
        assert ResultDictUtil.hash(a.to_dict()) == ResultDictUtil.hash(b.to_dict())


class TestNormalize:
    def test_remaps_edge_binding_ids(self):
        r = _result(
            "n0",
            "CHEBI:1",
            [Analysis(resource_id="infores:x", edge_bindings={"e0": [_eb("old")]})],
        )
        r_dict = r.to_dict()
        mapping = {"old": "new"}
        r.normalize(mapping)
        ResultDictUtil.normalize(r_dict, mapping)
        assert r_dict == r.to_dict()

    def test_normalize_list_parity(self):
        results = [
            _result(
                "n0",
                "CHEBI:1",
                [Analysis(resource_id="infores:x", edge_bindings={"e0": [_eb("old")]})],
            )
        ]
        dicts = [r.to_dict() for r in results]
        mapping = {"old": "new"}
        Result.normalize_list(results, mapping)
        ResultDictUtil.normalize_list(dicts, mapping)
        assert dicts == [r.to_dict() for r in results]


class TestUpdate:
    def test_merges_analyses(self):
        r = _result(
            "n0",
            "CHEBI:1",
            [Analysis(resource_id="infores:x", edge_bindings={"e0": [_eb("kg0")]})],
        )
        other = _result(
            "n0",
            "CHEBI:1",
            [
                Analysis(resource_id="infores:x", edge_bindings={"e0": [_eb("kg1")]}),
                Analysis(resource_id="infores:y", edge_bindings={}),
            ],
        )
        r_dict = r.to_dict()
        r.update(other)
        ResultDictUtil.update(r_dict, other.to_dict())
        assert _dict_analysis_hashes(r_dict) == _model_analysis_hashes(r)

    def test_empty_other_is_noop(self):
        r = _result("n0", "CHEBI:1", [Analysis(resource_id="infores:x", edge_bindings={})])
        r_dict = r.to_dict()
        ResultDictUtil.update(r_dict, {"node_bindings": {}, "analyses": []})
        assert _dict_analysis_hashes(r_dict) == _model_analysis_hashes(r)

    def test_dedupes_internal_duplicate_analyses_in_other(self):
        # `other` carries two equal-hash analyses absent from self; assert the absolute
        # dedup (count), not just parity, since the bug was identical on both sides.
        r = _result(
            "n0", "CHEBI:1", [Analysis(resource_id="infores:x", edge_bindings={})]
        )
        other = _result(
            "n0",
            "CHEBI:1",
            [
                Analysis(resource_id="infores:y", edge_bindings={}),
                Analysis(resource_id="infores:y", edge_bindings={}),
            ],
        )
        r_dict = r.to_dict()
        r.update(other)
        ResultDictUtil.update(r_dict, other.to_dict())
        assert len(r.analyses) == 2
        assert len(r_dict["analyses"]) == 2
        assert _dict_analysis_hashes(r_dict) == _model_analysis_hashes(r)


class TestMergeResults:
    def test_parity(self):
        results = [
            _result("n0", "CHEBI:1", [Analysis(resource_id="infores:x", edge_bindings={})]),
            _result("n0", "CHEBI:2", []),
        ]
        new = [
            # Same node bindings as results[0] -> merges analyses.
            _result("n0", "CHEBI:1", [Analysis(resource_id="infores:y", edge_bindings={})]),
        ]
        dicts = [r.to_dict() for r in results]
        new_dicts = [r.to_dict() for r in new]
        Result.merge_results(results, new)
        ResultDictUtil.merge_results(dicts, new_dicts)
        assert [ResultDictUtil.hash(d) for d in dicts] == [r.hash() for r in results]
        for d, r in zip(dicts, results, strict=True):
            assert _dict_analysis_hashes(d) == _model_analysis_hashes(r)


class TestMergeAnalysesByResourceId:
    def test_parity(self):
        r = _result(
            "n0",
            "CHEBI:1",
            [
                Analysis(resource_id="infores:x", edge_bindings={"e0": [_eb("kg0")]}),
                Analysis(resource_id="infores:x", edge_bindings={"e1": [_eb("kg1")]}),
                Analysis(resource_id="infores:y", edge_bindings={}),
            ],
        )
        r_dict = r.to_dict()
        r.merge_analyses_by_resource_id()
        ResultDictUtil.merge_analyses_by_resource_id(r_dict)
        assert _dict_analysis_hashes(r_dict) == _model_analysis_hashes(r)


class TestUpdateExistingAnalysisMerge:
    def test_same_hash_analysis_merged_not_appended(self):
        # identical hash-relevant fields but different attributes (not in the analysis
        # hash) -> the existing-analysis merge branch of update(), attributes combined
        a = _result(
            "n0",
            "CHEBI:1",
            [
                Analysis(
                    resource_id="infores:x",
                    edge_bindings={},
                    attributes=[Attribute(attribute_type_id="biolink:a", value=1)],
                )
            ],
        )
        other = _result(
            "n0",
            "CHEBI:1",
            [
                Analysis(
                    resource_id="infores:x",
                    edge_bindings={},
                    attributes=[Attribute(attribute_type_id="biolink:b", value=2)],
                )
            ],
        )
        r_dict = a.to_dict()
        a.update(other)
        ResultDictUtil.update(r_dict, other.to_dict())
        assert len(r_dict["analyses"]) == 1
        assert len(a.analyses) == 1
        assert _dict_analysis_hashes(r_dict) == _model_analysis_hashes(a)
        assert len(r_dict["analyses"][0].get("attributes", [])) == 2
