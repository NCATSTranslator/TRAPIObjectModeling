from __future__ import annotations

from typing import Literal

from pydantic import JsonValue
from typing_extensions import NotRequired, TypedDict

from translator_tom.models.shared import Infores, QEdgeID, QNodeID
from translator_tom.models.workflow_operations import (
    AboveOrBelow,
    AscendingOrDescending,
    PlusOrMinus,
    TopOrBottom,
)

__all__ = [
    "AllowListDict",
    "AnnotateEdgesParametersDict",
    "AnnotateNodesParametersDict",
    "BaseOperationDict",
    "DenyListDict",
    "EnrichResultsParametersDict",
    "FillAllowListParametersDict",
    "FillDenyListParametersDict",
    "FilterKgraphContinuousKedgeAttributeParametersDict",
    "FilterKgraphDiscreteKedgeAttributeParametersDict",
    "FilterKgraphDiscreteKnodeAttributeParametersDict",
    "FilterKgraphParametersBaseDict",
    "FilterKgraphPercentileParametersDict",
    "FilterKgraphStdDevParametersDict",
    "FilterKgraphTopNParametersDict",
    "FilterResultsTopNParametersDict",
    "OperationAnnotateDict",
    "OperationAnnotateEdgesDict",
    "OperationAnnotateNodesDict",
    "OperationBindDict",
    "OperationCompleteResultsDict",
    "OperationDict",
    "OperationEnrichResultsDict",
    "OperationFillDict",
    "OperationFilterKgraphContinuousKedgeAttributeDict",
    "OperationFilterKgraphDict",
    "OperationFilterKgraphDiscreteKedgeAttributeDict",
    "OperationFilterKgraphDiscreteKnodeAttributeDict",
    "OperationFilterKgraphOrphansDict",
    "OperationFilterKgraphPercentileDict",
    "OperationFilterKgraphStdDevDict",
    "OperationFilterKgraphTopNDict",
    "OperationFilterResultsDict",
    "OperationFilterResultsTopNDict",
    "OperationLookupAndScoreDict",
    "OperationLookupDict",
    "OperationOverlayComputeJaccardDict",
    "OperationOverlayComputeNgdDict",
    "OperationOverlayConnectKnodesDict",
    "OperationOverlayDict",
    "OperationOverlayFisherExactTestDict",
    "OperationParametersDict",
    "OperationRestateDict",
    "OperationScoreDict",
    "OperationSortResultsDict",
    "OperationSortResultsEdgeAttributeDict",
    "OperationSortResultsNodeAttributeDict",
    "OperationSortResultsScoreDict",
    "OverlayComputeJaccardParametersDict",
    "OverlayComputeNgdParametersDict",
    "OverlayFisherExactTestParametersDict",
    "RunnerParametersDict",
    "SortResultNodeAttributeParametersDict",
    "SortResultsEdgeAttributeParametersDict",
    "SortResultsScoreParametersDict",
]


class AllowListDict(TypedDict):
    allowlist: list[Infores]


class DenyListDict(TypedDict):
    denylist: list[Infores]


RunnerParametersDict = AllowListDict | DenyListDict


class OperationParametersDict(TypedDict):
    pass


class BaseOperationDict(TypedDict):
    runner_parameters: NotRequired[RunnerParametersDict | None]


class OperationAnnotateDict(BaseOperationDict):
    id: Literal["annotate"]
    parameters: NotRequired[dict[str, JsonValue] | None]


class AnnotateEdgesParametersDict(OperationParametersDict):
    attributes: NotRequired[list[str] | None]


class OperationAnnotateEdgesDict(BaseOperationDict):
    id: Literal["annotate_edges"]
    parameters: NotRequired[AnnotateEdgesParametersDict | None]


class AnnotateNodesParametersDict(OperationParametersDict):
    attributes: list[str] | None


class OperationAnnotateNodesDict(BaseOperationDict):
    id: Literal["annotate_nodes"]
    parameters: NotRequired[AnnotateNodesParametersDict | None]


class OperationBindDict(BaseOperationDict):
    id: Literal["bind"]
    parameters: NotRequired[dict[str, JsonValue] | None]


class OperationCompleteResultsDict(BaseOperationDict):
    id: Literal["complete_results"]
    parameters: NotRequired[dict[str, JsonValue] | None]


class EnrichResultsParametersDict(OperationParametersDict):
    pvalue_threshold: NotRequired[int | float | None]
    qnode_keys: NotRequired[list[QNodeID] | None]


class OperationEnrichResultsDict(BaseOperationDict):
    id: Literal["enrich_results"]
    parameters: NotRequired[EnrichResultsParametersDict | None]


class FillAllowListParametersDict(AllowListDict):
    qedge_keys: NotRequired[list[QEdgeID] | None]


class FillDenyListParametersDict(DenyListDict):
    qedge_keys: NotRequired[list[QEdgeID] | None]


class OperationFillDict(BaseOperationDict):
    id: Literal["fill"]
    parameters: NotRequired[
        FillAllowListParametersDict | FillDenyListParametersDict | None
    ]


class OperationFilterKgraphDict(BaseOperationDict):
    id: Literal["filter_kgraph"]
    parameters: NotRequired[dict[str, JsonValue] | None]


class FilterKgraphParametersBaseDict(OperationParametersDict):
    qedge_keys: list[QEdgeID] | None
    qnode_keys: NotRequired[list[QNodeID] | None]


class FilterKgraphContinuousKedgeAttributeParametersDict(
    FilterKgraphParametersBaseDict
):
    edge_attribute: str
    threshold: float
    remove_above_or_below: AboveOrBelow


class OperationFilterKgraphContinuousKedgeAttributeDict(BaseOperationDict):
    id: Literal["filter_kgraph_continuous_kedge_attribute"]
    parameters: FilterKgraphContinuousKedgeAttributeParametersDict


class FilterKgraphDiscreteKedgeAttributeParametersDict(FilterKgraphParametersBaseDict):
    edge_attribute: str
    remove_value: JsonValue


class OperationFilterKgraphDiscreteKedgeAttributeDict(BaseOperationDict):
    id: Literal["filter_kgraph_discrete_kedge_attribute"]
    parameters: FilterKgraphDiscreteKedgeAttributeParametersDict


class FilterKgraphDiscreteKnodeAttributeParametersDict(FilterKgraphParametersBaseDict):
    node_attribute: str
    remove_value: JsonValue


class OperationFilterKgraphDiscreteKnodeAttributeDict(BaseOperationDict):
    id: Literal["filter_kgraph_discrete_knode_attribute"]
    parameters: FilterKgraphDiscreteKnodeAttributeParametersDict


class OperationFilterKgraphOrphansDict(BaseOperationDict):
    id: Literal["filter_kgraph_orphans"]
    parameters: NotRequired[dict[str, JsonValue] | None]


class FilterKgraphPercentileParametersDict(FilterKgraphParametersBaseDict):
    edge_attribute: str
    threshold: NotRequired[float | None]
    remove_above_or_below: NotRequired[AboveOrBelow]


class OperationFilterKgraphPercentileDict(BaseOperationDict):
    id: Literal["filter_kgraph_percentile"]
    parameters: FilterKgraphPercentileParametersDict


class FilterKgraphStdDevParametersDict(FilterKgraphParametersBaseDict):
    edge_attribute: str
    num_sigma: NotRequired[float | None]
    remove_above_or_below: NotRequired[AboveOrBelow | None]
    plus_or_minus_std_dev: NotRequired[PlusOrMinus | None]


class OperationFilterKgraphStdDevDict(BaseOperationDict):
    id: Literal["filter_kgraph_std_dev"]
    parameters: FilterKgraphStdDevParametersDict


class FilterKgraphTopNParametersDict(FilterKgraphParametersBaseDict):
    edge_attribute: str
    max_edges: NotRequired[int | None]
    keep_top_or_bottom: NotRequired[TopOrBottom | None]


class OperationFilterKgraphTopNDict(BaseOperationDict):
    id: Literal["filter_kgraph_top_n"]
    parameters: FilterKgraphTopNParametersDict


class OperationFilterResultsDict(BaseOperationDict):
    id: Literal["filter_results"]
    parameters: NotRequired[dict[str, JsonValue] | None]


class FilterResultsTopNParametersDict(OperationParametersDict):
    max_results: int


class OperationFilterResultsTopNDict(BaseOperationDict):
    id: Literal["filter_results_top_n"]
    parameters: FilterResultsTopNParametersDict


class OperationLookupDict(BaseOperationDict):
    id: Literal["lookup"]
    parameters: NotRequired[dict[str, JsonValue] | None]


class OperationLookupAndScoreDict(BaseOperationDict):
    id: Literal["lookup_and_score"]
    parameters: NotRequired[dict[str, JsonValue] | None]


class OperationOverlayDict(BaseOperationDict):
    id: Literal["overlay"]
    parameters: NotRequired[dict[str, JsonValue] | None]


class OverlayComputeJaccardParametersDict(OperationParametersDict):
    intermediate_node_key: QNodeID
    end_node_keys: list[QNodeID]
    virtual_relation_label: QEdgeID


class OperationOverlayComputeJaccardDict(BaseOperationDict):
    id: Literal["overlay_compute_jaccard"]
    parameters: OverlayComputeJaccardParametersDict


class OverlayComputeNgdParametersDict(OperationParametersDict):
    virtual_relation_label: str
    qnode_keys: list[QNodeID]


class OperationOverlayComputeNgdDict(BaseOperationDict):
    id: Literal["overlay_compute_ngd"]
    parameters: OverlayComputeNgdParametersDict


class OperationOverlayConnectKnodesDict(BaseOperationDict):
    id: Literal["overlay_connect_knodes"]
    parameters: NotRequired[dict[str, JsonValue] | None]


class OverlayFisherExactTestParametersDict(OperationParametersDict):
    subject_qnode_key: QNodeID
    object_qnode_key: QNodeID
    virtual_relation_label: str
    rel_edge_key: QEdgeID | None


class OperationOverlayFisherExactTestDict(BaseOperationDict):
    id: Literal["overlay_fisher_exact_test"]
    parameters: OverlayFisherExactTestParametersDict


class OperationRestateDict(BaseOperationDict):
    id: Literal["restate"]
    parameters: NotRequired[dict[str, JsonValue] | None]


class OperationScoreDict(BaseOperationDict):
    id: Literal["score"]
    parameters: NotRequired[dict[str, JsonValue] | None]


class OperationSortResultsDict(BaseOperationDict):
    id: Literal["sort_results"]
    parameters: NotRequired[dict[str, JsonValue] | None]


class SortResultsEdgeAttributeParametersDict(OperationParametersDict):
    edge_attribute: str
    ascending_or_descending: AscendingOrDescending
    qedge_keys: list[QEdgeID]


class OperationSortResultsEdgeAttributeDict(BaseOperationDict):
    id: Literal["sort_results_edge_attribute"]
    parameters: SortResultsEdgeAttributeParametersDict


class SortResultNodeAttributeParametersDict(OperationParametersDict):
    node_attribute: str
    ascending_or_descending: AscendingOrDescending
    qnode_keys: list[QNodeID] | None


class OperationSortResultsNodeAttributeDict(BaseOperationDict):
    id: Literal["sort_results_node_attribute"]
    parameters: SortResultNodeAttributeParametersDict


class SortResultsScoreParametersDict(OperationParametersDict):
    ascending_or_descending: AscendingOrDescending


class OperationSortResultsScoreDict(BaseOperationDict):
    id: Literal["sort_results_score"]
    parameters: SortResultsScoreParametersDict


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
