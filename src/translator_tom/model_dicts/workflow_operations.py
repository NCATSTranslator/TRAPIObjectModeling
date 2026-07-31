from __future__ import annotations

from collections.abc import Mapping
from typing import ClassVar, Literal

from pydantic import JsonValue
from typing_extensions import NotRequired, TypedDict

from translator_tom.models.shared import Infores, QEdgeID, QNodeID
from translator_tom.models.workflow_operations import (
    AboveOrBelow,
    AllowList,
    AnnotateEdgesParameters,
    AnnotateNodesParameters,
    AscendingOrDescending,
    BaseOperation,
    DenyList,
    EnrichResultsParameters,
    FillAllowListParameters,
    FillDenyListParameters,
    FilterKgraphContinuousKedgeAttributeParameters,
    FilterKgraphDiscreteKedgeAttributeParameters,
    FilterKgraphDiscreteKnodeAttributeParameters,
    FilterKgraphParametersBase,
    FilterKgraphPercentileParameters,
    FilterKgraphStdDevParameters,
    FilterKgraphTopNParameters,
    FilterResultsTopNParameters,
    OperationAnnotate,
    OperationAnnotateEdges,
    OperationAnnotateNodes,
    OperationBind,
    OperationCompleteResults,
    OperationEnrichResults,
    OperationFill,
    OperationFilterKgraph,
    OperationFilterKgraphContinuousKedgeAttribute,
    OperationFilterKgraphDiscreteKedgeAttribute,
    OperationFilterKgraphDiscreteKnodeAttribute,
    OperationFilterKgraphOrphans,
    OperationFilterKgraphPercentile,
    OperationFilterKgraphStdDev,
    OperationFilterKgraphTopN,
    OperationFilterResults,
    OperationFilterResultsTopN,
    OperationLookup,
    OperationLookupAndScore,
    OperationOverlay,
    OperationOverlayComputeJaccard,
    OperationOverlayComputeNgd,
    OperationOverlayConnectKnodes,
    OperationOverlayFisherExactTest,
    OperationRestate,
    OperationScore,
    OperationSortResults,
    OperationSortResultsEdgeAttribute,
    OperationSortResultsNodeAttribute,
    OperationSortResultsScore,
    OverlayComputeJaccardParameters,
    OverlayComputeNgdParameters,
    OverlayFisherExactTestParameters,
    PlusOrMinus,
    SortResultNodeAttributeParameters,
    SortResultsEdgeAttributeParameters,
    SortResultsScoreParameters,
    TopOrBottom,
)
from translator_tom.utils.dict_util_base import DictUtil, register_union_discriminator

__all__ = [
    "AllowListDict",
    "AllowListDictUtil",
    "AnnotateEdgesParametersDict",
    "AnnotateEdgesParametersDictUtil",
    "AnnotateNodesParametersDict",
    "AnnotateNodesParametersDictUtil",
    "BaseOperationDict",
    "BaseOperationDictUtil",
    "DenyListDict",
    "DenyListDictUtil",
    "EnrichResultsParametersDict",
    "EnrichResultsParametersDictUtil",
    "FillAllowListParametersDict",
    "FillAllowListParametersDictUtil",
    "FillDenyListParametersDict",
    "FillDenyListParametersDictUtil",
    "FilterKgraphContinuousKedgeAttributeParametersDict",
    "FilterKgraphContinuousKedgeAttributeParametersDictUtil",
    "FilterKgraphDiscreteKedgeAttributeParametersDict",
    "FilterKgraphDiscreteKedgeAttributeParametersDictUtil",
    "FilterKgraphDiscreteKnodeAttributeParametersDict",
    "FilterKgraphDiscreteKnodeAttributeParametersDictUtil",
    "FilterKgraphParametersBaseDict",
    "FilterKgraphParametersBaseDictUtil",
    "FilterKgraphPercentileParametersDict",
    "FilterKgraphPercentileParametersDictUtil",
    "FilterKgraphStdDevParametersDict",
    "FilterKgraphStdDevParametersDictUtil",
    "FilterKgraphTopNParametersDict",
    "FilterKgraphTopNParametersDictUtil",
    "FilterResultsTopNParametersDict",
    "FilterResultsTopNParametersDictUtil",
    "OperationAnnotateDict",
    "OperationAnnotateDictUtil",
    "OperationAnnotateEdgesDict",
    "OperationAnnotateEdgesDictUtil",
    "OperationAnnotateNodesDict",
    "OperationAnnotateNodesDictUtil",
    "OperationBindDict",
    "OperationBindDictUtil",
    "OperationCompleteResultsDict",
    "OperationCompleteResultsDictUtil",
    "OperationDict",
    "OperationEnrichResultsDict",
    "OperationEnrichResultsDictUtil",
    "OperationFillDict",
    "OperationFillDictUtil",
    "OperationFilterKgraphContinuousKedgeAttributeDict",
    "OperationFilterKgraphContinuousKedgeAttributeDictUtil",
    "OperationFilterKgraphDict",
    "OperationFilterKgraphDictUtil",
    "OperationFilterKgraphDiscreteKedgeAttributeDict",
    "OperationFilterKgraphDiscreteKedgeAttributeDictUtil",
    "OperationFilterKgraphDiscreteKnodeAttributeDict",
    "OperationFilterKgraphDiscreteKnodeAttributeDictUtil",
    "OperationFilterKgraphOrphansDict",
    "OperationFilterKgraphOrphansDictUtil",
    "OperationFilterKgraphPercentileDict",
    "OperationFilterKgraphPercentileDictUtil",
    "OperationFilterKgraphStdDevDict",
    "OperationFilterKgraphStdDevDictUtil",
    "OperationFilterKgraphTopNDict",
    "OperationFilterKgraphTopNDictUtil",
    "OperationFilterResultsDict",
    "OperationFilterResultsDictUtil",
    "OperationFilterResultsTopNDict",
    "OperationFilterResultsTopNDictUtil",
    "OperationLookupAndScoreDict",
    "OperationLookupAndScoreDictUtil",
    "OperationLookupDict",
    "OperationLookupDictUtil",
    "OperationOverlayComputeJaccardDict",
    "OperationOverlayComputeJaccardDictUtil",
    "OperationOverlayComputeNgdDict",
    "OperationOverlayComputeNgdDictUtil",
    "OperationOverlayConnectKnodesDict",
    "OperationOverlayConnectKnodesDictUtil",
    "OperationOverlayDict",
    "OperationOverlayDictUtil",
    "OperationOverlayFisherExactTestDict",
    "OperationOverlayFisherExactTestDictUtil",
    "OperationRestateDict",
    "OperationRestateDictUtil",
    "OperationScoreDict",
    "OperationScoreDictUtil",
    "OperationSortResultsDict",
    "OperationSortResultsDictUtil",
    "OperationSortResultsEdgeAttributeDict",
    "OperationSortResultsEdgeAttributeDictUtil",
    "OperationSortResultsNodeAttributeDict",
    "OperationSortResultsNodeAttributeDictUtil",
    "OperationSortResultsScoreDict",
    "OperationSortResultsScoreDictUtil",
    "OverlayComputeJaccardParametersDict",
    "OverlayComputeJaccardParametersDictUtil",
    "OverlayComputeNgdParametersDict",
    "OverlayComputeNgdParametersDictUtil",
    "OverlayFisherExactTestParametersDict",
    "OverlayFisherExactTestParametersDictUtil",
    "RunnerParametersDict",
    "SortResultNodeAttributeParametersDict",
    "SortResultNodeAttributeParametersDictUtil",
    "SortResultsEdgeAttributeParametersDict",
    "SortResultsEdgeAttributeParametersDictUtil",
    "SortResultsScoreParametersDict",
    "SortResultsScoreParametersDictUtil",
]


class AllowListDict(TypedDict):
    allowlist: list[Infores]


class AllowListDictUtil(DictUtil[AllowListDict]):
    """Registration-only util for `AllowListDict`."""

    _model = AllowList


class DenyListDict(TypedDict):
    denylist: list[Infores]


class DenyListDictUtil(DictUtil[DenyListDict]):
    """Registration-only util for `DenyListDict`."""

    _model = DenyList


RunnerParametersDict = AllowListDict | DenyListDict


class OperationParametersDict(TypedDict):
    pass


class BaseOperationDict(TypedDict):
    runner_parameters: NotRequired[RunnerParametersDict | None]


class BaseOperationDictUtil(DictUtil[BaseOperationDict]):
    """Utility methods for `BaseOperationDict`, mirroring those on the `BaseOperation` model."""

    _model = BaseOperation
    _unique: ClassVar[bool] = False

    @classmethod
    def unique(cls) -> bool:
        """Whether the operation may produce different results depending on the agent."""
        return cls._unique


class OperationAnnotateDict(BaseOperationDict):
    id: Literal["annotate"]
    parameters: NotRequired[dict[str, JsonValue] | None]


class OperationAnnotateDictUtil(BaseOperationDictUtil):
    """Utility methods for `OperationAnnotateDict`, mirroring the `OperationAnnotate` model."""

    _model = OperationAnnotate
    _unique = True


class AnnotateEdgesParametersDict(OperationParametersDict):
    attributes: NotRequired[list[str] | None]


class AnnotateEdgesParametersDictUtil(DictUtil[AnnotateEdgesParametersDict]):
    """Utility methods for `AnnotateEdgesParametersDict`, mirroring the model."""

    _model = AnnotateEdgesParameters

    @staticmethod
    def attributes_list(parameters: AnnotateEdgesParametersDict) -> list[str]:
        """Get the attributes as a guaranteed list, even if they are represented as None."""
        attributes = parameters.get("attributes")
        return attributes if attributes is not None else []


class OperationAnnotateEdgesDict(BaseOperationDict):
    id: Literal["annotate_edges"]
    parameters: NotRequired[AnnotateEdgesParametersDict | None]


class OperationAnnotateEdgesDictUtil(BaseOperationDictUtil):
    """Utility methods for `OperationAnnotateEdgesDict`, mirroring the model."""

    _model = OperationAnnotateEdges
    _unique = True


class AnnotateNodesParametersDict(OperationParametersDict):
    attributes: list[str] | None


class AnnotateNodesParametersDictUtil(DictUtil[AnnotateNodesParametersDict]):
    """Utility methods for `AnnotateNodesParametersDict`, mirroring the model."""

    _model = AnnotateNodesParameters

    @staticmethod
    def attributes_list(parameters: AnnotateNodesParametersDict) -> list[str]:
        """Get the attributes as a guaranteed list, even if they are represented as None."""
        attributes = parameters.get("attributes")
        return attributes if attributes is not None else []


class OperationAnnotateNodesDict(BaseOperationDict):
    id: Literal["annotate_nodes"]
    parameters: NotRequired[AnnotateNodesParametersDict | None]


class OperationAnnotateNodesDictUtil(BaseOperationDictUtil):
    """Utility methods for `OperationAnnotateNodesDict`, mirroring the model."""

    _model = OperationAnnotateNodes
    _unique = True


class OperationBindDict(BaseOperationDict):
    id: Literal["bind"]
    parameters: NotRequired[dict[str, JsonValue] | None]


class OperationBindDictUtil(BaseOperationDictUtil):
    """Utility methods for `OperationBindDict`, mirroring the `OperationBind` model."""

    _model = OperationBind


class OperationCompleteResultsDict(BaseOperationDict):
    id: Literal["complete_results"]
    parameters: NotRequired[dict[str, JsonValue] | None]


class OperationCompleteResultsDictUtil(BaseOperationDictUtil):
    """Utility methods for `OperationCompleteResultsDict`, mirroring the model."""

    _model = OperationCompleteResults


class EnrichResultsParametersDict(OperationParametersDict):
    pvalue_threshold: NotRequired[int | float]
    qnode_keys: NotRequired[list[QNodeID] | None]


class EnrichResultsParametersDictUtil(DictUtil[EnrichResultsParametersDict]):
    """Utility methods for `EnrichResultsParametersDict`, mirroring the model."""

    _model = EnrichResultsParameters

    @staticmethod
    def qnode_keys_list(parameters: EnrichResultsParametersDict) -> list[QNodeID]:
        """Return a guaranteed list of qnode_keys, empty if it is not defined."""
        qnode_keys = parameters.get("qnode_keys")
        return qnode_keys if qnode_keys is not None else []


class OperationEnrichResultsDict(BaseOperationDict):
    id: Literal["enrich_results"]
    parameters: NotRequired[EnrichResultsParametersDict | None]


class OperationEnrichResultsDictUtil(BaseOperationDictUtil):
    """Utility methods for `OperationEnrichResultsDict`, mirroring the model."""

    _model = OperationEnrichResults
    _unique = True


class FillAllowListParametersDict(AllowListDict):
    qedge_keys: NotRequired[list[QEdgeID] | None]


class FillAllowListParametersDictUtil(DictUtil[FillAllowListParametersDict]):
    """Utility methods for `FillAllowListParametersDict`, mirroring the model."""

    _model = FillAllowListParameters

    @staticmethod
    def qedge_keys_list(parameters: FillAllowListParametersDict) -> list[QEdgeID]:
        """Return a guaranteed list of qedge_keys, empty if it is not defined."""
        qedge_keys = parameters.get("qedge_keys")
        return qedge_keys if qedge_keys is not None else []


class FillDenyListParametersDict(DenyListDict):
    qedge_keys: NotRequired[list[QEdgeID] | None]


class FillDenyListParametersDictUtil(DictUtil[FillDenyListParametersDict]):
    """Utility methods for `FillDenyListParametersDict`, mirroring the model."""

    _model = FillDenyListParameters

    @staticmethod
    def qedge_keys_list(parameters: FillDenyListParametersDict) -> list[QEdgeID]:
        """Return a guaranteed list of qedge_keys, empty if it is not defined."""
        qedge_keys = parameters.get("qedge_keys")
        return qedge_keys if qedge_keys is not None else []


class OperationFillDict(BaseOperationDict):
    id: Literal["fill"]
    parameters: NotRequired[
        FillAllowListParametersDict | FillDenyListParametersDict | None
    ]


class OperationFillDictUtil(BaseOperationDictUtil):
    """Utility methods for `OperationFillDict`, mirroring the `OperationFill` model."""

    _model = OperationFill
    _unique = True


class OperationFilterKgraphDict(BaseOperationDict):
    id: Literal["filter_kgraph"]
    parameters: NotRequired[dict[str, JsonValue] | None]


class OperationFilterKgraphDictUtil(BaseOperationDictUtil):
    """Utility methods for `OperationFilterKgraphDict`, mirroring the model."""

    _model = OperationFilterKgraph


class FilterKgraphParametersBaseDict(OperationParametersDict):
    qedge_keys: list[QEdgeID] | None
    qnode_keys: NotRequired[list[QNodeID]]


class FilterKgraphParametersBaseDictUtil(DictUtil[FilterKgraphParametersBaseDict]):
    """Utility methods for `FilterKgraphParametersBaseDict`, mirroring the model."""

    _model = FilterKgraphParametersBase

    @staticmethod
    def qedge_keys_list(parameters: FilterKgraphParametersBaseDict) -> list[QEdgeID]:
        """Return a guaranteed list of qedge_keys, empty if it is not defined."""
        qedge_keys = parameters.get("qedge_keys")
        return qedge_keys if qedge_keys is not None else []

    @staticmethod
    def qnode_keys_list(parameters: FilterKgraphParametersBaseDict) -> list[QNodeID]:
        """Return a guaranteed list of qnode_keys, empty if it is not defined."""
        qnode_keys = parameters.get("qnode_keys")
        return qnode_keys if qnode_keys is not None else []


class FilterKgraphContinuousKedgeAttributeParametersDict(
    FilterKgraphParametersBaseDict
):
    edge_attribute: str
    threshold: float
    remove_above_or_below: AboveOrBelow


class FilterKgraphContinuousKedgeAttributeParametersDictUtil(
    FilterKgraphParametersBaseDictUtil
):
    """Utility methods for `FilterKgraphContinuousKedgeAttributeParametersDict`."""

    _model = FilterKgraphContinuousKedgeAttributeParameters


class OperationFilterKgraphContinuousKedgeAttributeDict(BaseOperationDict):
    id: Literal["filter_kgraph_continuous_kedge_attribute"]
    parameters: FilterKgraphContinuousKedgeAttributeParametersDict


class OperationFilterKgraphContinuousKedgeAttributeDictUtil(BaseOperationDictUtil):
    """Utility methods for `OperationFilterKgraphContinuousKedgeAttributeDict`."""

    _model = OperationFilterKgraphContinuousKedgeAttribute


class FilterKgraphDiscreteKedgeAttributeParametersDict(FilterKgraphParametersBaseDict):
    edge_attribute: str
    remove_value: JsonValue


class FilterKgraphDiscreteKedgeAttributeParametersDictUtil(
    FilterKgraphParametersBaseDictUtil
):
    """Utility methods for `FilterKgraphDiscreteKedgeAttributeParametersDict`."""

    _model = FilterKgraphDiscreteKedgeAttributeParameters


class OperationFilterKgraphDiscreteKedgeAttributeDict(BaseOperationDict):
    id: Literal["filter_kgraph_discrete_kedge_attribute"]
    parameters: FilterKgraphDiscreteKedgeAttributeParametersDict


class OperationFilterKgraphDiscreteKedgeAttributeDictUtil(BaseOperationDictUtil):
    """Utility methods for `OperationFilterKgraphDiscreteKedgeAttributeDict`."""

    _model = OperationFilterKgraphDiscreteKedgeAttribute


class FilterKgraphDiscreteKnodeAttributeParametersDict(FilterKgraphParametersBaseDict):
    node_attribute: str
    remove_value: JsonValue


class FilterKgraphDiscreteKnodeAttributeParametersDictUtil(
    FilterKgraphParametersBaseDictUtil
):
    """Utility methods for `FilterKgraphDiscreteKnodeAttributeParametersDict`."""

    _model = FilterKgraphDiscreteKnodeAttributeParameters


class OperationFilterKgraphDiscreteKnodeAttributeDict(BaseOperationDict):
    id: Literal["filter_kgraph_discrete_knode_attribute"]
    parameters: FilterKgraphDiscreteKnodeAttributeParametersDict


class OperationFilterKgraphDiscreteKnodeAttributeDictUtil(BaseOperationDictUtil):
    """Utility methods for `OperationFilterKgraphDiscreteKnodeAttributeDict`."""

    _model = OperationFilterKgraphDiscreteKnodeAttribute


class OperationFilterKgraphOrphansDict(BaseOperationDict):
    id: Literal["filter_kgraph_orphans"]
    parameters: NotRequired[dict[str, JsonValue] | None]


class OperationFilterKgraphOrphansDictUtil(BaseOperationDictUtil):
    """Utility methods for `OperationFilterKgraphOrphansDict`, mirroring the model."""

    _model = OperationFilterKgraphOrphans


class FilterKgraphPercentileParametersDict(FilterKgraphParametersBaseDict):
    edge_attribute: str
    threshold: NotRequired[float]
    remove_above_or_below: NotRequired[AboveOrBelow]


class FilterKgraphPercentileParametersDictUtil(FilterKgraphParametersBaseDictUtil):
    """Utility methods for `FilterKgraphPercentileParametersDict`."""

    _model = FilterKgraphPercentileParameters


class OperationFilterKgraphPercentileDict(BaseOperationDict):
    id: Literal["filter_kgraph_percentile"]
    parameters: FilterKgraphPercentileParametersDict


class OperationFilterKgraphPercentileDictUtil(BaseOperationDictUtil):
    """Utility methods for `OperationFilterKgraphPercentileDict`, mirroring the model."""

    _model = OperationFilterKgraphPercentile


class FilterKgraphStdDevParametersDict(FilterKgraphParametersBaseDict):
    edge_attribute: str
    num_sigma: NotRequired[float]
    remove_above_or_below: NotRequired[AboveOrBelow]
    plus_or_minus_std_dev: NotRequired[PlusOrMinus]


class FilterKgraphStdDevParametersDictUtil(FilterKgraphParametersBaseDictUtil):
    """Utility methods for `FilterKgraphStdDevParametersDict`."""

    _model = FilterKgraphStdDevParameters


class OperationFilterKgraphStdDevDict(BaseOperationDict):
    id: Literal["filter_kgraph_std_dev"]
    parameters: FilterKgraphStdDevParametersDict


class OperationFilterKgraphStdDevDictUtil(BaseOperationDictUtil):
    """Utility methods for `OperationFilterKgraphStdDevDict`, mirroring the model."""

    _model = OperationFilterKgraphStdDev


class FilterKgraphTopNParametersDict(FilterKgraphParametersBaseDict):
    edge_attribute: str
    max_edges: NotRequired[int]
    keep_top_or_bottom: NotRequired[TopOrBottom]


class FilterKgraphTopNParametersDictUtil(FilterKgraphParametersBaseDictUtil):
    """Utility methods for `FilterKgraphTopNParametersDict`."""

    _model = FilterKgraphTopNParameters


class OperationFilterKgraphTopNDict(BaseOperationDict):
    id: Literal["filter_kgraph_top_n"]
    parameters: FilterKgraphTopNParametersDict


class OperationFilterKgraphTopNDictUtil(BaseOperationDictUtil):
    """Utility methods for `OperationFilterKgraphTopNDict`, mirroring the model."""

    _model = OperationFilterKgraphTopN


class OperationFilterResultsDict(BaseOperationDict):
    id: Literal["filter_results"]
    parameters: NotRequired[dict[str, JsonValue] | None]


class OperationFilterResultsDictUtil(BaseOperationDictUtil):
    """Utility methods for `OperationFilterResultsDict`, mirroring the model."""

    _model = OperationFilterResults


class FilterResultsTopNParametersDict(OperationParametersDict):
    max_results: int


class FilterResultsTopNParametersDictUtil(DictUtil[FilterResultsTopNParametersDict]):
    """Registration-only util for `FilterResultsTopNParametersDict`."""

    _model = FilterResultsTopNParameters


class OperationFilterResultsTopNDict(BaseOperationDict):
    id: Literal["filter_results_top_n"]
    parameters: FilterResultsTopNParametersDict


class OperationFilterResultsTopNDictUtil(BaseOperationDictUtil):
    """Utility methods for `OperationFilterResultsTopNDict`, mirroring the model."""

    _model = OperationFilterResultsTopN


class OperationLookupDict(BaseOperationDict):
    id: Literal["lookup"]
    parameters: NotRequired[dict[str, JsonValue] | None]


class OperationLookupDictUtil(BaseOperationDictUtil):
    """Utility methods for `OperationLookupDict`, mirroring the `OperationLookup` model."""

    _model = OperationLookup
    _unique = True


class OperationLookupAndScoreDict(BaseOperationDict):
    id: Literal["lookup_and_score"]
    parameters: NotRequired[dict[str, JsonValue] | None]


class OperationLookupAndScoreDictUtil(BaseOperationDictUtil):
    """Utility methods for `OperationLookupAndScoreDict`, mirroring the model."""

    _model = OperationLookupAndScore
    _unique = True


class OperationOverlayDict(BaseOperationDict):
    id: Literal["overlay"]
    parameters: NotRequired[dict[str, JsonValue] | None]


class OperationOverlayDictUtil(BaseOperationDictUtil):
    """Utility methods for `OperationOverlayDict`, mirroring the `OperationOverlay` model."""

    _model = OperationOverlay


class OverlayComputeJaccardParametersDict(OperationParametersDict):
    intermediate_node_key: QNodeID
    end_node_keys: list[QNodeID]
    virtual_relation_label: QEdgeID


class OverlayComputeJaccardParametersDictUtil(
    DictUtil[OverlayComputeJaccardParametersDict]
):
    """Registration-only util for `OverlayComputeJaccardParametersDict`."""

    _model = OverlayComputeJaccardParameters


class OperationOverlayComputeJaccardDict(BaseOperationDict):
    id: Literal["overlay_compute_jaccard"]
    parameters: OverlayComputeJaccardParametersDict


class OperationOverlayComputeJaccardDictUtil(BaseOperationDictUtil):
    """Utility methods for `OperationOverlayComputeJaccardDict`, mirroring the model."""

    _model = OperationOverlayComputeJaccard


class OverlayComputeNgdParametersDict(OperationParametersDict):
    virtual_relation_label: str
    qnode_keys: list[QNodeID]


class OverlayComputeNgdParametersDictUtil(DictUtil[OverlayComputeNgdParametersDict]):
    """Registration-only util for `OverlayComputeNgdParametersDict`."""

    _model = OverlayComputeNgdParameters


class OperationOverlayComputeNgdDict(BaseOperationDict):
    id: Literal["overlay_compute_ngd"]
    parameters: OverlayComputeNgdParametersDict


class OperationOverlayComputeNgdDictUtil(BaseOperationDictUtil):
    """Utility methods for `OperationOverlayComputeNgdDict`, mirroring the model."""

    _model = OperationOverlayComputeNgd


class OperationOverlayConnectKnodesDict(BaseOperationDict):
    id: Literal["overlay_connect_knodes"]
    parameters: NotRequired[dict[str, JsonValue] | None]


class OperationOverlayConnectKnodesDictUtil(BaseOperationDictUtil):
    """Utility methods for `OperationOverlayConnectKnodesDict`, mirroring the model."""

    _model = OperationOverlayConnectKnodes


class OverlayFisherExactTestParametersDict(OperationParametersDict):
    subject_qnode_key: QNodeID
    object_qnode_key: QNodeID
    virtual_relation_label: str
    rel_edge_key: QEdgeID | None


class OverlayFisherExactTestParametersDictUtil(
    DictUtil[OverlayFisherExactTestParametersDict]
):
    """Registration-only util for `OverlayFisherExactTestParametersDict`."""

    _model = OverlayFisherExactTestParameters


class OperationOverlayFisherExactTestDict(BaseOperationDict):
    id: Literal["overlay_fisher_exact_test"]
    parameters: OverlayFisherExactTestParametersDict


class OperationOverlayFisherExactTestDictUtil(BaseOperationDictUtil):
    """Utility methods for `OperationOverlayFisherExactTestDict`, mirroring the model."""

    _model = OperationOverlayFisherExactTest


class OperationRestateDict(BaseOperationDict):
    id: Literal["restate"]
    parameters: NotRequired[dict[str, JsonValue] | None]


class OperationRestateDictUtil(BaseOperationDictUtil):
    """Utility methods for `OperationRestateDict`, mirroring the `OperationRestate` model."""

    _model = OperationRestate
    _unique = True


class OperationScoreDict(BaseOperationDict):
    id: Literal["score"]
    parameters: NotRequired[dict[str, JsonValue] | None]


class OperationScoreDictUtil(BaseOperationDictUtil):
    """Utility methods for `OperationScoreDict`, mirroring the `OperationScore` model."""

    _model = OperationScore
    _unique = True


class OperationSortResultsDict(BaseOperationDict):
    id: Literal["sort_results"]
    parameters: NotRequired[dict[str, JsonValue] | None]


class OperationSortResultsDictUtil(BaseOperationDictUtil):
    """Utility methods for `OperationSortResultsDict`, mirroring the model."""

    _model = OperationSortResults


class SortResultsEdgeAttributeParametersDict(OperationParametersDict):
    edge_attribute: str
    ascending_or_descending: AscendingOrDescending
    qedge_keys: list[QEdgeID]


class SortResultsEdgeAttributeParametersDictUtil(
    DictUtil[SortResultsEdgeAttributeParametersDict]
):
    """Registration-only util for `SortResultsEdgeAttributeParametersDict`."""

    _model = SortResultsEdgeAttributeParameters


class OperationSortResultsEdgeAttributeDict(BaseOperationDict):
    id: Literal["sort_results_edge_attribute"]
    parameters: SortResultsEdgeAttributeParametersDict


class OperationSortResultsEdgeAttributeDictUtil(BaseOperationDictUtil):
    """Utility methods for `OperationSortResultsEdgeAttributeDict`, mirroring the model."""

    _model = OperationSortResultsEdgeAttribute


class SortResultNodeAttributeParametersDict(OperationParametersDict):
    node_attribute: str
    ascending_or_descending: AscendingOrDescending
    qnode_keys: list[QNodeID] | None


class SortResultNodeAttributeParametersDictUtil(
    DictUtil[SortResultNodeAttributeParametersDict]
):
    """Utility methods for `SortResultNodeAttributeParametersDict`, mirroring the model."""

    _model = SortResultNodeAttributeParameters

    @staticmethod
    def qnode_keys_list(
        parameters: SortResultNodeAttributeParametersDict,
    ) -> list[QNodeID]:
        """Return a guaranteed list of qnode_keys, empty if it is not defined."""
        qnode_keys = parameters.get("qnode_keys")
        return qnode_keys if qnode_keys is not None else []


class OperationSortResultsNodeAttributeDict(BaseOperationDict):
    id: Literal["sort_results_node_attribute"]
    parameters: SortResultNodeAttributeParametersDict


class OperationSortResultsNodeAttributeDictUtil(BaseOperationDictUtil):
    """Utility methods for `OperationSortResultsNodeAttributeDict`, mirroring the model."""

    _model = OperationSortResultsNodeAttribute


class SortResultsScoreParametersDict(OperationParametersDict):
    ascending_or_descending: AscendingOrDescending


class SortResultsScoreParametersDictUtil(DictUtil[SortResultsScoreParametersDict]):
    """Registration-only util for `SortResultsScoreParametersDict`."""

    _model = SortResultsScoreParameters


class OperationSortResultsScoreDict(BaseOperationDict):
    id: Literal["sort_results_score"]
    parameters: SortResultsScoreParametersDict


class OperationSortResultsScoreDictUtil(BaseOperationDictUtil):
    """Utility methods for `OperationSortResultsScoreDict`, mirroring the model."""

    _model = OperationSortResultsScore


OperationDict = (
    OperationAnnotateDict
    | OperationAnnotateEdgesDict
    | OperationAnnotateNodesDict
    | OperationBindDict
    | OperationCompleteResultsDict
    | OperationEnrichResultsDict
    | OperationFillDict
    | OperationFilterKgraphDict
    | OperationFilterKgraphContinuousKedgeAttributeDict
    | OperationFilterKgraphDiscreteKedgeAttributeDict
    | OperationFilterKgraphDiscreteKnodeAttributeDict
    | OperationFilterKgraphOrphansDict
    | OperationFilterKgraphPercentileDict
    | OperationFilterKgraphStdDevDict
    | OperationFilterKgraphTopNDict
    | OperationFilterResultsDict
    | OperationFilterResultsTopNDict
    | OperationLookupDict
    | OperationLookupAndScoreDict
    | OperationOverlayDict
    | OperationOverlayComputeJaccardDict
    | OperationOverlayComputeNgdDict
    | OperationOverlayConnectKnodesDict
    | OperationOverlayFisherExactTestDict
    | OperationRestateDict
    | OperationScoreDict
    | OperationSortResultsDict
    | OperationSortResultsEdgeAttributeDict
    | OperationSortResultsNodeAttributeDict
    | OperationSortResultsScoreDict
)


def _discriminate_runner_parameters(
    value: Mapping[str, object],
) -> type[AllowList | DenyList]:
    """Pick the concrete runner-parameters model (`allowlist` key -> AllowList)."""
    return AllowList if "allowlist" in value else DenyList


def _discriminate_fill_parameters(
    value: Mapping[str, object],
) -> type[FillAllowListParameters | FillDenyListParameters]:
    """Pick the concrete fill-parameters model (`allowlist` key -> FillAllowList)."""
    return FillAllowListParameters if "allowlist" in value else FillDenyListParameters


# `BaseOperation.runner_parameters` and `OperationFill.parameters` are structural
# (non-tagged) unions, so hashing an operation needs explicit discriminators.
register_union_discriminator((AllowList, DenyList), _discriminate_runner_parameters)
register_union_discriminator(
    (FillAllowListParameters, FillDenyListParameters), _discriminate_fill_parameters
)
