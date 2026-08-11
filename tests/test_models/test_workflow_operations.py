"""Targeted tests for translator_tom.models.workflow_operations.

End-to-end deserialization is already exercised by tests/test_workflow.py;
this file fills coverage gaps for `unique` overrides, list-getter properties
on parameter classes, the simple enums, and AllowList/DenyList min_length.
"""

import pytest
from pydantic import TypeAdapter, ValidationError

from translator_tom.models.workflow_operations import (
    AboveOrBelowEnum,
    AllowList,
    AnnotateEdgesParameters,
    AnnotateNodesParameters,
    Operation,
    AscendingOrDescendingEnum,
    DenyList,
    EnrichResultsParameters,
    FillAllowListParameters,
    FillDenyListParameters,
    FilterKgraphContinuousKedgeAttributeParameters,
    OperationAnnotate,
    OperationAnnotateEdges,
    OperationAnnotateNodes,
    OperationBind,
    OperationEnrichResults,
    OperationFill,
    OperationLookup,
    OperationLookupAndScore,
    OperationRestate,
    OperationScore,
    PlusOrMinusEnum,
    SortResultNodeAttributeParameters,
    TopOrBottomEnum,
)


# ============================================================================
# Enums
# ============================================================================


class TestEnums:
    def test_ascending_or_descending(self):
        assert AscendingOrDescendingEnum.ascending.value == "ascending"
        assert AscendingOrDescendingEnum.descending.value == "descending"

    def test_above_or_below(self):
        assert AboveOrBelowEnum.above.value == "above"
        assert AboveOrBelowEnum.below.value == "below"

    def test_plus_or_minus(self):
        assert PlusOrMinusEnum.plus.value == "plus"
        assert PlusOrMinusEnum.minus.value == "minus"

    def test_top_or_bottom(self):
        assert TopOrBottomEnum.top.value == "top"
        assert TopOrBottomEnum.bottom.value == "bottom"


# ============================================================================
# AllowList / DenyList
# ============================================================================


class TestAllowList:
    def test_constructs(self):
        a = AllowList(allowlist=["infores:aragorn"])
        assert a.allowlist == ["infores:aragorn"]

    def test_min_length_enforced(self):
        with pytest.raises(ValidationError):
            AllowList(allowlist=[])


class TestDenyList:
    def test_constructs(self):
        d = DenyList(denylist=["infores:aragorn"])
        assert d.denylist == ["infores:aragorn"]

    def test_min_length_enforced(self):
        with pytest.raises(ValidationError):
            DenyList(denylist=[])


# ============================================================================
# `unique` property
# ============================================================================


class TestUniqueProperty:
    def test_default_is_false(self):
        # OperationBind does not override `unique`, so it inherits BaseOperation.
        op = OperationBind(id="bind")
        assert op.unique is False

    @pytest.mark.parametrize(
        "op",
        [
            OperationAnnotate(id="annotate"),
            OperationAnnotateEdges(id="annotate_edges"),
            OperationAnnotateNodes(id="annotate_nodes"),
            OperationEnrichResults(id="enrich_results"),
            OperationFill(id="fill"),
            OperationLookup(id="lookup"),
            OperationLookupAndScore(id="lookup_and_score"),
            OperationRestate(id="restate"),
            OperationScore(id="score"),
        ],
    )
    def test_unique_overridden_to_true(self, op: OperationAnnotate):
        assert op.unique is True


# ============================================================================
# List-getter properties on parameter classes
# ============================================================================


class TestAnnotateEdgesParameters:
    def test_attributes_list_when_none(self):
        assert AnnotateEdgesParameters().attributes_list == []

    def test_attributes_list_when_set(self):
        p = AnnotateEdgesParameters(attributes=["pmids"])
        assert p.attributes_list == ["pmids"]


class TestAnnotateNodesParameters:
    def test_attributes_list_when_none(self):
        assert AnnotateNodesParameters(attributes=None).attributes_list == []

    def test_attributes_list_when_set(self):
        p = AnnotateNodesParameters(attributes=["pmids"])
        assert p.attributes_list == ["pmids"]


class TestEnrichResultsParameters:
    def test_qnode_keys_list_when_none(self):
        assert EnrichResultsParameters().qnode_keys_list == []

    def test_qnode_keys_list_when_set(self):
        p = EnrichResultsParameters(qnode_keys=["n01"])
        assert p.qnode_keys_list == ["n01"]


class TestFillAllowListParameters:
    def test_qedge_keys_list_when_none(self):
        p = FillAllowListParameters(allowlist=["infores:foo"])
        assert p.qedge_keys_list == []

    def test_qedge_keys_list_when_set(self):
        p = FillAllowListParameters(
            allowlist=["infores:foo"], qedge_keys=["e00"]
        )
        assert p.qedge_keys_list == ["e00"]


class TestFillDenyListParameters:
    def test_qedge_keys_list_when_none(self):
        p = FillDenyListParameters(denylist=["infores:foo"])
        assert p.qedge_keys_list == []

    def test_qedge_keys_list_when_set(self):
        p = FillDenyListParameters(
            denylist=["infores:foo"], qedge_keys=["e00"]
        )
        assert p.qedge_keys_list == ["e00"]


class TestFilterKgraphParametersBase:
    """Exercises qedge_keys_list / qnode_keys_list defined on the shared base."""

    def _make(
        self,
        *,
        qedge_keys: list[str] | None = None,
        qnode_keys: list[str] | None = None,
    ) -> FilterKgraphContinuousKedgeAttributeParameters:
        # qnode_keys is non-nullable (defaults to []); only pass it when provided.
        kwargs: dict[str, object] = {
            "edge_attribute": "normalized_google_distance",
            "threshold": 1.0,
            "remove_above_or_below": "above",
            "qedge_keys": qedge_keys,
        }
        if qnode_keys is not None:
            kwargs["qnode_keys"] = qnode_keys
        return FilterKgraphContinuousKedgeAttributeParameters(**kwargs)

    def test_qedge_keys_list_when_none(self):
        assert self._make().qedge_keys_list == []

    def test_qedge_keys_list_when_set(self):
        assert self._make(qedge_keys=["e0"]).qedge_keys_list == ["e0"]

    def test_qnode_keys_list_when_omitted_defaults_empty(self):
        assert self._make().qnode_keys_list == []

    def test_qnode_keys_list_when_set(self):
        assert self._make(qnode_keys=["n0"]).qnode_keys_list == ["n0"]


class TestSortResultNodeAttributeParameters:
    def test_qnode_keys_list_when_none(self):
        p = SortResultNodeAttributeParameters(
            node_attribute="x",
            ascending_or_descending="ascending",
            qnode_keys=None,
        )
        assert p.qnode_keys_list == []

    def test_qnode_keys_list_when_set(self):
        p = SortResultNodeAttributeParameters(
            node_attribute="x",
            ascending_or_descending="ascending",
            qnode_keys=["n0"],
        )
        assert p.qnode_keys_list == ["n0"]


# ============================================================================
# Optional parameters default to None when omitted (regression)
# ============================================================================


class TestOptionalParametersDefaultNone:
    """These previously-required optional fields must now default to None."""

    _op = TypeAdapter(Operation)

    def test_annotate_nodes_attributes_omitted(self):
        # from_dict on the param model, and via the discriminated Operation union.
        assert AnnotateNodesParameters.from_dict({}).attributes is None
        op = self._op.validate_python({"id": "annotate_nodes", "parameters": {}})
        assert op.parameters.attributes is None
        assert self._op.validate_python(op.to_dict()).parameters.attributes is None

    def test_filter_kgraph_percentile_qedge_keys_omitted(self):
        op = self._op.validate_python(
            {"id": "filter_kgraph_percentile", "parameters": {"edge_attribute": "ngd"}}
        )
        assert op.parameters.qedge_keys is None
        assert self._op.validate_python(op.to_dict()).parameters.qedge_keys is None

    def test_overlay_fisher_exact_test_rel_edge_key_omitted(self):
        op = self._op.validate_python(
            {
                "id": "overlay_fisher_exact_test",
                "parameters": {
                    "subject_qnode_key": "n1",
                    "object_qnode_key": "n2",
                    "virtual_relation_label": "f1",
                },
            }
        )
        assert op.parameters.rel_edge_key is None
        assert self._op.validate_python(op.to_dict()).parameters.rel_edge_key is None
