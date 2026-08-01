"""Parity tests for the workflow-operation `*DictUtil` classes."""

from __future__ import annotations

from translator_tom.model_dicts.workflow_operations import (
    AnnotateEdgesParametersDict,
    AnnotateEdgesParametersDictUtil,
    EnrichResultsParametersDict,
    EnrichResultsParametersDictUtil,
    FillAllowListParametersDict,
    FillAllowListParametersDictUtil,
    FilterKgraphPercentileParametersDict,
    FilterKgraphPercentileParametersDictUtil,
    FilterKgraphStdDevParametersDictUtil,
    OperationBindDictUtil,
    OperationFillDictUtil,
    OperationFilterKgraphPercentileDictUtil,
    OperationFilterKgraphStdDevDictUtil,
    OperationScoreDictUtil,
    SortResultNodeAttributeParametersDict,
    SortResultNodeAttributeParametersDictUtil,
)
from translator_tom.models.workflow_operations import (
    AllowList,
    DenyList,
    FillAllowListParameters,
    FillDenyListParameters,
    FilterKgraphPercentileParameters,
    FilterKgraphStdDevParameters,
    OperationBind,
    OperationFill,
    OperationFilterKgraphPercentile,
    OperationFilterKgraphStdDev,
    OperationScore,
)


class TestUnique:
    def test_matches_model(self):
        assert OperationBindDictUtil.unique() == OperationBind(id="bind").unique
        assert OperationScoreDictUtil.unique() == OperationScore(id="score").unique
        assert OperationFillDictUtil.unique() == OperationFill(id="fill").unique

    def test_values(self):
        assert OperationBindDictUtil.unique() is False
        assert OperationScoreDictUtil.unique() is True


class TestParameterListAccessors:
    def test_annotate_edges_attributes(self):
        params: AnnotateEdgesParametersDict = {"attributes": ["pmids"]}
        assert AnnotateEdgesParametersDictUtil.attributes_list(params) == ["pmids"]
        assert AnnotateEdgesParametersDictUtil.attributes_list({}) == []

    def test_enrich_results_qnode_keys(self):
        params: EnrichResultsParametersDict = {"qnode_keys": ["n0"]}
        assert EnrichResultsParametersDictUtil.qnode_keys_list(params) == ["n0"]
        assert EnrichResultsParametersDictUtil.qnode_keys_list({}) == []

    def test_fill_allowlist_qedge_keys(self):
        params: FillAllowListParametersDict = {
            "allowlist": ["infores:x"],
            "qedge_keys": ["e0"],
        }
        assert FillAllowListParametersDictUtil.qedge_keys_list(params) == ["e0"]

    def test_filter_kgraph_base_accessors_inherited(self):
        # FilterKgraphPercentileParametersDictUtil inherits the base accessors.
        params: FilterKgraphPercentileParametersDict = {
            "qedge_keys": ["e0"],
            "qnode_keys": ["n0"],
            "edge_attribute": "x",
        }
        assert FilterKgraphPercentileParametersDictUtil.qedge_keys_list(params) == [
            "e0"
        ]
        assert FilterKgraphPercentileParametersDictUtil.qnode_keys_list(params) == [
            "n0"
        ]

    def test_sort_node_attribute_qnode_keys(self):
        params: SortResultNodeAttributeParametersDict = {
            "node_attribute": "x",
            "ascending_or_descending": "ascending",
            "qnode_keys": None,
        }
        assert SortResultNodeAttributeParametersDictUtil.qnode_keys_list(params) == []


class TestOperationHashParity:
    def test_simple_operation(self):
        op = OperationScore(id="score")
        assert OperationScoreDictUtil.hash(op.to_dict()) == op.hash()

    def test_runner_parameters_allowlist_union(self):
        op = OperationBind(id="bind", runner_parameters=AllowList(allowlist=["infores:a"]))
        assert OperationBindDictUtil.hash(op.to_dict()) == op.hash()

    def test_runner_parameters_denylist_union(self):
        op = OperationBind(id="bind", runner_parameters=DenyList(denylist=["infores:a"]))
        assert OperationBindDictUtil.hash(op.to_dict()) == op.hash()

    def test_fill_allowlist_parameters_union(self):
        op = OperationFill(
            id="fill",
            runner_parameters=AllowList(allowlist=["infores:a"]),
            parameters=FillAllowListParameters(
                allowlist=["infores:b"], qedge_keys=["e0"]
            ),
        )
        assert OperationFillDictUtil.hash(op.to_dict()) == op.hash()

    def test_fill_denylist_parameters_union(self):
        op = OperationFill(
            id="fill",
            parameters=FillDenyListParameters(denylist=["infores:b"]),
        )
        assert OperationFillDictUtil.hash(op.to_dict()) == op.hash()


class TestFilterKgraphParamHashParity:
    """Regression: `threshold`/`num_sigma` are float fields; their defaults must be
    floats so exclude_defaults drops-and-restores them without an int/float hash drift.
    """

    def test_percentile_threshold(self):
        # default 95.0 (dropped by exclude_defaults) + an explicit non-default value
        default = FilterKgraphPercentileParameters(qedge_keys=["e0"], edge_attribute="a")
        explicit = FilterKgraphPercentileParameters(
            qedge_keys=["e0"], edge_attribute="a", threshold=50.0
        )
        for m in (default, explicit):
            assert FilterKgraphPercentileParametersDictUtil.hash(m.to_dict()) == m.hash()

    def test_stddev_num_sigma(self):
        default = FilterKgraphStdDevParameters(qedge_keys=["e0"], edge_attribute="a")
        explicit = FilterKgraphStdDevParameters(
            qedge_keys=["e0"], edge_attribute="a", num_sigma=2.0
        )
        for m in (default, explicit):
            assert FilterKgraphStdDevParametersDictUtil.hash(m.to_dict()) == m.hash()

    def test_operation_wrappers_at_default(self):
        pct = OperationFilterKgraphPercentile(
            id="filter_kgraph_percentile",
            parameters=FilterKgraphPercentileParameters(
                qedge_keys=["e0"], edge_attribute="a"
            ),
        )
        assert OperationFilterKgraphPercentileDictUtil.hash(pct.to_dict()) == pct.hash()
        std = OperationFilterKgraphStdDev(
            id="filter_kgraph_std_dev",
            parameters=FilterKgraphStdDevParameters(
                qedge_keys=["e0"], edge_attribute="a"
            ),
        )
        assert OperationFilterKgraphStdDevDictUtil.hash(std.to_dict()) == std.hash()
