from __future__ import annotations

from typing import Any

from translator_tom.models.auxiliary_graph import AuxiliaryGraphsDict
from translator_tom.models.knowledge_graph import KnowledgeGraph
from translator_tom.models.meta_knowledge_graph import MetaKnowledgeGraph
from translator_tom.models.query_graph import PathfinderQueryGraph, QueryGraph
from translator_tom.models.workflow_operations import (
    EnrichResultsParameters,
    FillAllowListParameters,
    FillDenyListParameters,
    FilterKgraphParametersBase,
    OperationEnrichResults,
    OperationFill,
    OperationFilterKgraphContinuousKedgeAttribute,
    OperationFilterKgraphDiscreteKedgeAttribute,
    OperationFilterKgraphDiscreteKnodeAttribute,
    OperationFilterKgraphPercentile,
    OperationFilterKgraphStdDev,
    OperationFilterKgraphTopN,
    OperationOverlayComputeJaccard,
    OperationOverlayComputeNgd,
    OperationOverlayFisherExactTest,
    OperationSortResultsEdgeAttribute,
    OperationSortResultsNodeAttribute,
    OverlayComputeJaccardParameters,
    OverlayComputeNgdParameters,
    OverlayFisherExactTestParameters,
    SortResultNodeAttributeParameters,
    SortResultsEdgeAttributeParameters,
)
from translator_tom.validation._util import (
    Location,
    SemanticValidationResult,
    always_valid,
    extend_location,
    semantic_validate,
    validate_keys_exist,
    validation_pipeline,
)

# --- Operation types: delegate to their parameters ---


@semantic_validate.register(OperationEnrichResults)
@semantic_validate.register(OperationFill)
@semantic_validate.register(OperationFilterKgraphContinuousKedgeAttribute)
@semantic_validate.register(OperationFilterKgraphDiscreteKedgeAttribute)
@semantic_validate.register(OperationFilterKgraphDiscreteKnodeAttribute)
@semantic_validate.register(OperationFilterKgraphPercentile)
@semantic_validate.register(OperationFilterKgraphStdDev)
@semantic_validate.register(OperationFilterKgraphTopN)
@semantic_validate.register(OperationOverlayComputeJaccard)
@semantic_validate.register(OperationOverlayComputeNgd)
@semantic_validate.register(OperationOverlayFisherExactTest)
@semantic_validate.register(OperationSortResultsEdgeAttribute)
@semantic_validate.register(OperationSortResultsNodeAttribute)
def _validate_op_with_params(  # noqa: PLR0913
    obj: Any,
    location: Location | None = None,
    *,
    kgraph: KnowledgeGraph | None = None,
    qgraph: QueryGraph | PathfinderQueryGraph | None = None,
    aux_graphs: AuxiliaryGraphsDict | None = None,
    metakg: MetaKnowledgeGraph | None = None,
    **_: Any,
) -> SemanticValidationResult:
    return semantic_validate(
        obj.parameters,
        location=location,
        kgraph=kgraph,
        qgraph=qgraph,
        aux_graphs=aux_graphs,
        metakg=metakg,
    )


# --- Parameter types: cross-model checks ---


@semantic_validate.register(EnrichResultsParameters)
def _validate_enrich_results_params(
    obj: EnrichResultsParameters,
    location: Location | None = None,
    *,
    qgraph: QueryGraph | PathfinderQueryGraph | None = None,
    **_: Any,
) -> SemanticValidationResult:
    return (
        validate_keys_exist(
            obj.qnode_keys_list,
            qgraph.nodes.keys(),
            "QNode",
            "query_graph",
            extend_location(location, "qnode_keys"),
        )
        if qgraph is not None
        else always_valid()
    )


@semantic_validate.register(FillAllowListParameters)
def _validate_fill_allow_list_params(
    obj: FillAllowListParameters,
    location: Location | None = None,
    *,
    qgraph: QueryGraph | PathfinderQueryGraph | None = None,
    **_: Any,
) -> SemanticValidationResult:
    return (
        validate_keys_exist(
            obj.qedge_keys_list,
            qgraph.edges.keys(),
            "QEdge",
            "query_graph",
            extend_location(location, "qedge_keys"),
        )
        if qgraph is not None and isinstance(qgraph, QueryGraph)
        else always_valid()
    )


@semantic_validate.register(FillDenyListParameters)
def _validate_fill_deny_list_params(
    obj: FillDenyListParameters,
    location: Location | None = None,
    *,
    qgraph: QueryGraph | PathfinderQueryGraph | None = None,
    **_: Any,
) -> SemanticValidationResult:
    return (
        validate_keys_exist(
            obj.qedge_keys_list,
            qgraph.edges.keys(),
            "QEdge",
            "query_graph",
            extend_location(location, "qedge_keys"),
        )
        if qgraph is not None and isinstance(qgraph, QueryGraph)
        else always_valid()
    )


@semantic_validate.register(FilterKgraphParametersBase)
def _validate_filter_kgraph_params(
    obj: FilterKgraphParametersBase,
    location: Location | None = None,
    *,
    qgraph: QueryGraph | PathfinderQueryGraph | None = None,
    **_: Any,
) -> SemanticValidationResult:
    return validation_pipeline(
        (
            validate_keys_exist(
                obj.qedge_keys_list,
                qgraph.edges.keys(),
                "QEdge",
                "query_graph",
                extend_location(location, "qedge_keys"),
            )
            if qgraph is not None and isinstance(qgraph, QueryGraph)
            else always_valid()
        ),
        (
            validate_keys_exist(
                obj.qnode_keys_list,
                qgraph.nodes.keys(),
                "QNode",
                "query_graph",
                extend_location(location, "qnode_keys"),
            )
            if qgraph is not None
            else always_valid()
        ),
    )


@semantic_validate.register(OverlayComputeJaccardParameters)
def _validate_overlay_jaccard_params(
    obj: OverlayComputeJaccardParameters,
    location: Location | None = None,
    *,
    qgraph: QueryGraph | PathfinderQueryGraph | None = None,
    **_: Any,
) -> SemanticValidationResult:
    return validation_pipeline(
        (
            validate_keys_exist(
                [obj.intermediate_node_key],
                qgraph.nodes.keys(),
                "QNode",
                "query_graph",
                extend_location(location, "intermediate_node_key"),
            )
            if qgraph is not None
            else always_valid()
        ),
        (
            validate_keys_exist(
                obj.end_node_keys,
                qgraph.nodes.keys(),
                "QNode",
                "query_graph",
                extend_location(location, "end_node_keys"),
            )
            if qgraph is not None
            else always_valid()
        ),
        (
            validate_keys_exist(
                [obj.virtual_relation_label],
                qgraph.nodes.keys(),
                "QNode",
                "query_graph",
                extend_location(location, "virtual_relation_label"),
            )
            if qgraph is not None
            else always_valid()
        ),
    )


@semantic_validate.register(OverlayComputeNgdParameters)
def _validate_overlay_ngd_params(
    obj: OverlayComputeNgdParameters,
    location: Location | None = None,
    *,
    qgraph: QueryGraph | PathfinderQueryGraph | None = None,
    **_: Any,
) -> SemanticValidationResult:
    return (
        validate_keys_exist(
            obj.qnode_keys,
            qgraph.nodes.keys(),
            "QNode",
            "query_graph",
            extend_location(location, "qnode_keys"),
        )
        if qgraph is not None
        else always_valid()
    )


@semantic_validate.register(OverlayFisherExactTestParameters)
def _validate_overlay_fisher_params(
    obj: OverlayFisherExactTestParameters,
    location: Location | None = None,
    *,
    qgraph: QueryGraph | PathfinderQueryGraph | None = None,
    **_: Any,
) -> SemanticValidationResult:
    return validation_pipeline(
        (
            validate_keys_exist(
                [obj.subject_qnode_key],
                qgraph.nodes.keys(),
                "QNode",
                "query_graph",
                extend_location(location, "subject_qnode_key"),
            )
            if qgraph is not None
            else always_valid()
        ),
        (
            validate_keys_exist(
                [obj.object_qnode_key],
                qgraph.nodes.keys(),
                "QNode",
                "query_graph",
                extend_location(location, "object_qnode_key"),
            )
            if qgraph is not None
            else always_valid()
        ),
        (
            validate_keys_exist(
                [obj.rel_edge_key],
                qgraph.edges.keys(),
                "QEdge",
                "query_graph",
                extend_location(location, "rel_edge_key"),
            )
            if qgraph is not None
            and obj.rel_edge_key is not None
            and isinstance(qgraph, QueryGraph)
            else always_valid()
        ),
    )


@semantic_validate.register(SortResultsEdgeAttributeParameters)
def _validate_sort_edge_attr_params(
    obj: SortResultsEdgeAttributeParameters,
    location: Location | None = None,
    *,
    qgraph: QueryGraph | PathfinderQueryGraph | None = None,
    **_: Any,
) -> SemanticValidationResult:
    return (
        validate_keys_exist(
            obj.qedge_keys,
            qgraph.edges.keys(),
            "QEdge",
            "query_graph",
            extend_location(location, "qedge_keys"),
        )
        if qgraph is not None and isinstance(qgraph, QueryGraph)
        else always_valid()
    )


@semantic_validate.register(SortResultNodeAttributeParameters)
def _validate_sort_node_attr_params(
    obj: SortResultNodeAttributeParameters,
    location: Location | None = None,
    *,
    qgraph: QueryGraph | PathfinderQueryGraph | None = None,
    **_: Any,
) -> SemanticValidationResult:
    return (
        validate_keys_exist(
            obj.qnode_keys_list,
            qgraph.nodes.keys(),
            "QNode",
            "query_graph",
            extend_location(location, "qnode_keys"),
        )
        if qgraph is not None
        else always_valid()
    )
