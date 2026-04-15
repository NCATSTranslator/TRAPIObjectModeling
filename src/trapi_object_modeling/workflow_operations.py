from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal, override

from pydantic import ConfigDict, Field, JsonValue, SkipValidation
from pydantic.dataclasses import dataclass

from trapi_object_modeling.shared import Infores, QEdgeID, QNodeID
from trapi_object_modeling.utils.object_base import TOMBaseObject


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class AllowList(TOMBaseObject):
    """List of operation providers (by infores ID) that may be used to complete operation."""

    allowlist: Annotated[
        list[Infores], Field(min_length=1, examples=["infores:aragorn"])
    ]
    """List of operation providers (by infores ID) that may be used to complete operation.

    No others will be used. A full list of operation providers for each operation with
    infores ID's is available through the '/services' endpoint of the workflow runner.
    """


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class DenyList(TOMBaseObject):
    """List of operation providers (by infores ID) that may not be used to complete operation."""

    denylist: Annotated[
        list[Infores], Field(min_length=1, examples=["infores:aragorn"])
    ]
    """List of operation providers (by infores ID) that may not be used to complete operation.

    All others will be used. A full list of operation providers for each operation with
    infores ID's is available through the '/services' endpoint of the worflow runner.
    """


RunnerParameters = AllowList | DenyList


class AscendingOrDescending(str, Enum):
    """Indicates whether results should be sorted in ascending or descending order."""

    ascending = "ascending"
    descending = "descending"


AscendingOrDescendingValue = Literal["ascending", "descending"]


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationParameters(TOMBaseObject):
    """Base class for various operation parameters."""


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class WorkflowOperation(TOMBaseObject):
    """Base class for types of workflow operation to execute."""

    runner_parameters: RunnerParameters | None = None

    @property
    def unique(self) -> bool:
        """Asserts operation may produce different results depending on the agent."""
        return False


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationAnnotate(WorkflowOperation):
    """This operation adds attributes to knowledge graph elements."""

    id: Literal["annotate"]
    parameters: dict[str, SkipValidation[JsonValue]]

    @property
    @override
    def unique(self) -> bool:
        """Asserts operation may produce different results depending on the agent."""
        return True


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class AnnotateEdgesParameters(OperationParameters):
    """Parameters for the AnnotateEdges operation."""

    """A list of attributes to annotate the edges with."""

    attributes: Annotated[list[str] | None, Field(examples=["pmids"])] = None
    """A list of attributes to annotate the edges with.

    If not included then all available data will be annotated.
    """

    @property
    def attributes_list(self) -> list[str]:
        """Get the attributes as a guaranteed list, even if they are represented as None."""
        return self.attributes if self.attributes is not None else []


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationAnnotateEdges(WorkflowOperation):
    """This operation adds attributes to knowledge graph edges."""

    id: Literal["annotate_edges"]
    parameters: AnnotateEdgesParameters | None = None

    @property
    @override
    def unique(self) -> bool:
        """Asserts operation may produce different results depending on the agent."""
        return True


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class AnnotateNodesParameters(OperationParameters):
    """Parameters for the AnnotateNodes operation."""

    """A list of attributes to annotate the nodes with."""

    attributes: Annotated[list[str] | None, Field(examples=["pmids"])]
    """A list of attributes to annotate the nodes with.

    If not included then all available data will be annotated.
    """

    @property
    def attributes_list(self) -> list[str]:
        """Get the attributes as a guaranteed list, even if they are represented as None."""
        return self.attributes if self.attributes is not None else []


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationAnnotateNodes(WorkflowOperation):
    """This operation adds attributes to knowledge graph nodes."""

    id: Literal["annotate_nodes"]
    parameters: AnnotateNodesParameters | None = None

    @property
    @override
    def unique(self) -> bool:
        """Asserts operation may produce different results depending on the agent."""
        return True


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationBind(WorkflowOperation):
    """This operation adds results binding kgraph elements to qgraph elements."""

    id: Literal["bind"]
    parameters: dict[str, SkipValidation[JsonValue]]


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationCompleteResults(WorkflowOperation):
    """This operation combines partial results into complete results."""

    id: Literal["complete_results"]
    parameters: dict[str, SkipValidation[JsonValue]]


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class EnrichResultsParameters(OperationParameters):
    """Parameters for the EnrichResults operation."""

    pvalue_threshold: Annotated[
        int | float | None, Field(examples=[1e-7], ge=0, le=0)
    ] = 1e-6
    """The cutoff p-value for enrichment."""

    qnode_keys: Annotated[list[QNodeID] | None, Field(examples=["n01"])] = None
    """If specified, then only knodes bound to these qnodes will be examined for enrichment and combination."""

    @property
    def qnode_keys_list(self) -> list[QNodeID]:
        """Return a guaranteed list of qnode_keys, empty if it is not defined."""
        return self.qnode_keys if self.qnode_keys is not None else []


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationEnrichResults(WorkflowOperation):
    """Create new results by applying enrichment analysis to existing results.

    In particular, combines results by transforming a qnode into a set, formed of
    KNodes that share a property or relation more often than expected by chance.
    """

    id: Literal["enrich_results"]
    parameters: EnrichResultsParameters

    @property
    @override
    def unique(self) -> bool:
        """Asserts operation may produce different results depending on the agent."""
        return True


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class FillAllowListParameters(AllowList):
    """AllowList Parameters for the Fill operation."""

    qedge_keys: Annotated[list[QEdgeID] | None, Field(examples=["e00"])] = None
    """A list of qedge keys.

    If included only edges corresponding to the given qedge keys, as well as their
    connected nodes, will be filled. If not included all edges will be filled.
    """

    @property
    def qedge_keys_list(self) -> list[QNodeID]:
        """Return a guaranteed list of qedge_keys, empty if it is not defined."""
        return self.qedge_keys if self.qedge_keys is not None else []


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class FillDenyListParameters(DenyList):
    """DenyList Parameters for the Fill operation."""

    qedge_keys: Annotated[list[QEdgeID] | None, Field(examples=["e00"])] = None
    """A list of qedge keys.

    If included only edges corresponding to the given qedge keys, as well as their
    connected nodes, will be filled. If not included all edges will be filled.
    """

    @property
    def qedge_keys_list(self) -> list[QNodeID]:
        """Return a guaranteed list of qedge_keys, empty if it is not defined."""
        return self.qedge_keys if self.qedge_keys is not None else []


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationFill(WorkflowOperation):
    """This operation adds knodes and kedges. SkipValidation[JsonValue] constraints attached to QNodes and QEdges specified in the TRAPI must be respected."""

    id: Literal["fill"]
    parameters: FillAllowListParameters | FillDenyListParameters

    @property
    @override
    def unique(self) -> bool:
        """Asserts operation may produce different results depending on the agent."""
        return True


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationFilterKgraph(WorkflowOperation):
    """This operation removes kgraph elements (nodes and/or edges)."""

    id: Literal["filter_kgraph"]
    parameters: dict[str, SkipValidation[JsonValue]]


class AboveOrBelowEnum(str, Enum):
    """Above or below, used in FilterKgraphContinuous-style operations."""

    above = "above"
    below = "below"


AboveOrBelow = Literal["above", "below"]


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class FilterKgraphParametersBase(OperationParameters):
    """A base class for filtering the kgraph with appropriate validation."""

    qedge_keys: Annotated[list[QEdgeID] | None, Field(examples=["[e01]"])]
    """This indicates if you only want to remove edges with specific edge_keys.

    If not provided or empty, all edges will be filtered on.
    """

    qnode_keys: Annotated[
        list[QNodeID] | None, Field(examples=["[n01]"], default_factory=list)
    ]
    """This indicates if you only want nodes corresponding to a specific list of qnode_keys to be removed.

    If not provided or empty, no nodes will be removed when filtering. Allows us to
    know what to do with the nodes connected to edges that are removed.
    """

    @property
    def qedge_keys_list(self) -> list[QNodeID]:
        """Return a guaranteed list of qedge_keys, empty if it is not defined."""
        return self.qedge_keys if self.qedge_keys is not None else []

    @property
    def qnode_keys_list(self) -> list[QNodeID]:
        """Return a guaranteed list of qnode_keys, empty if it is not defined."""
        return self.qnode_keys if self.qnode_keys is not None else []


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class FilterKgraphContinuousKedgeAttributeParameters(FilterKgraphParametersBase):
    """Parameters for the FilterKgraphContinuousKedgeAttribute operation."""

    edge_attribute: Annotated[str, Field(examples=["normalized_google_distance"])]
    """The name of the edge attribute to filter on."""

    threshold: Annotated[float, Field(examples=["1.2"])]
    """The value to compare attribute values to."""

    remove_above_or_below: AboveOrBelow


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationFilterKgraphContinuousKedgeAttribute(WorkflowOperation):
    """This operation removes kgraph edges based on the value of a continuous edge attribute.

    Edges without the given attribute are left alone
    """

    id: Literal["filter_kgraph_continuous_kedge_attribute"]
    parameters: FilterKgraphContinuousKedgeAttributeParameters


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class FilterKgraphDiscreteKedgeAttributeParameters(FilterKgraphParametersBase):
    """Parameters for the FilterKgraphDiscreteKedgeAttribute operation."""

    edge_attribute: Annotated[str, Field(examples=["provided_by"])]
    """The name of the edge attribute to filter on."""

    remove_value: Annotated[
        SkipValidation[JsonValue], Field(examples=["infores:semmeddb"])
    ]
    """The value for which all edges containing this value in the specified edge_attribute should be removed."""


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationFilterKgraphDiscreteKedgeAttribute(WorkflowOperation):
    """This operation removes kgraph edges which have a discrete attribute containing the specified value.

    Edges without the given attribute are left alone
    """

    id: Literal["filter_kgraph_discrete_kedge_attribute"]
    parameters: FilterKgraphDiscreteKedgeAttributeParameters


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class FilterKgraphDiscreteKnodeAttributeParameters(FilterKgraphParametersBase):
    """Parameters for the FilterKgraphDiscreteKnodeAttribute operation."""

    node_attribute: Annotated[str, Field(examples=["molecule_type"])]
    """The name of the node attribute to filter on."""

    remove_value: Annotated[
        SkipValidation[JsonValue], Field(examples=["small_molecule"])
    ]
    """The value for which all edges containing this value in the specified edge_attribute should be removed."""


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationFilterKgraphDiscreteKnodeAttribute(WorkflowOperation):
    """This operation removes kgraph nodes which have a discrete attribute containing the specified value.

    In TRAPI 1.1+ this will look in the `attribute_type_id` and
    `original_attribute_name` attribute fields for the attribute name. Node without the
    given attribute are left alone. Edges connecting to the removed nodes will also be
    removed.
    """

    id: Literal["filter_kgraph_discrete_knode_attribute"]
    parameters: FilterKgraphDiscreteKnodeAttributeParameters


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationFilterKgraphOrphans(WorkflowOperation):
    """This operation removes kgraph elements that are not referenced by any results."""

    id: Literal["filter_kgraph_orphans"]
    parameters: dict[str, SkipValidation[JsonValue]]


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class FilterKgraphPercentileParameters(FilterKgraphParametersBase):
    """Parameters for the FilterKgraphPercentile operation."""

    edge_attribute: Annotated[str, Field(examples=["normalized_google_distance"])]
    """The name of the edge attribute to filter on."""

    threshold: Annotated[float | None, Field(gt=0, le=100, examples=[96.8])] = 95
    """The percentile to threshold on."""

    remove_above_or_below: AboveOrBelow = "below"
    """Indicates whether to remove above or below the given threshold."""


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationFilterKgraphPercentile(WorkflowOperation):
    """This operation removes kgraph edges that have attribute values are below/above the given percentile."""

    id: Literal["filter_kgraph_percentile"]
    parameters: FilterKgraphPercentileParameters


class PlusOrMinusEnum(str, Enum):
    """Plus or minus, used in FilterKgraphStdDevParameters."""

    plus = "plus"
    minus = "minus"


PlusOrMinus = Literal["plus", "minus"]


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class FilterKgraphStdDevParameters(FilterKgraphParametersBase):
    """Parameters for the FilterKgraphStdDev operation."""

    edge_attribute: Annotated[str, Field(examples=["normalized_google_distance"])]
    """The name of the edge attribute to filter on."""

    num_sigma: Annotated[float | None, Field(gt=0, examples=[1.2])] = 1
    """The number of standard deviations to threshold on."""

    remove_above_or_below: AboveOrBelow | None = "below"
    """Indictes whether to remove above or below the given threshold."""

    plus_or_minus_std_dev: PlusOrMinus | None = "plus"
    """Indicate whether or not the threshold should be found using plus or minus the standard deviation.

    E.g. when plus_or_minus_std_dev is set to plus will set the cutoff for filtering as
    the mean + num_sigma * std_dev while setting plus_or_minus_std_dev to minus will
    set the cutoff as the mean - num_sigma * std_dev.
    """


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationFilterKgraphStdDev(WorkflowOperation):
    """This operation removes kgraph edges that have attribute values are below/above the mean +/- n standard deviations."""

    id: Literal["filter_kgraph_std_dev"]
    parameters: FilterKgraphStdDevParameters


class TopOrBottomEnum(str, Enum):
    """Top or Bottom, used in TopN-style operations."""

    top = "top"
    bottom = "bottom"


TopOrBottom = Literal["top", "bottom"]


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class FilterKgraphTopNParameters(FilterKgraphParametersBase):
    """Parameters for the FilterKgraphTopN operation."""

    edge_attribute: Annotated[str, Field(examples=["normalized_google_distance"])]
    """The name of the edge attribute to filter on."""

    max_edges: Annotated[int | None, Field(gt=0, examples=[10])] = 50
    """The number of edges to keep."""

    keep_top_or_bottom: TopOrBottom | None = "top"
    """Indicate whether or not the the top or bottom n values should be kept."""


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationFilterKgraphTopN(WorkflowOperation):
    """This operation removes kgraph edges that have attribute values are below/above the top/bottom n values."""

    id: Literal["filter_kgraph_top_n"]
    parameters: FilterKgraphTopNParameters


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationFilterResults(WorkflowOperation):
    """This operation allows the TRAPI server to remove elements from the list of results."""

    id: Literal["filter_results"]
    parameters: dict[str, SkipValidation[JsonValue]]


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class FilterResultsTopNParameters(OperationParameters):
    """Parameters for the FilterResultsTopN operation."""

    max_results: Annotated[int, Field(gt=0, examples=[50])]


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationFilterResultsTopN(WorkflowOperation):
    """This operation truncates the results to at most `max_results` that appear in the TRAPI JSON message."""

    id: Literal["filter_results_top_n"]
    parameters: FilterResultsTopNParameters


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationLookup(WorkflowOperation):
    """This operation adds knodes/kedges and (complete) results.

    It is equivalent to the workflow fill + bind + complete_results. SkipValidation[JsonValue] constraints
    attached to QNodes and QEdges specified in the TRAPI must be respected.
    """

    id: Literal["lookup"]
    parameters: dict[str, SkipValidation[JsonValue]]

    @property
    @override
    def unique(self) -> bool:
        """Asserts operation may produce different results depending on the agent."""
        return True


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationLookupAndScore(WorkflowOperation):
    """This operation adds knodes/kedges, (complete) results, and scores (to the results).

    It is equivalent to the workflow fill + bind + complete_results + score. SkipValidation[JsonValue]
    constraints attached to QNodes and QEdges specified in the TRAPI must be respected.
    """

    id: Literal["lookup_and_score"]
    parameters: dict[str, SkipValidation[JsonValue]]

    @property
    @override
    def unique(self) -> bool:
        """Asserts operation may produce different results depending on the agent."""
        return True


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationOverlay(WorkflowOperation):
    """This operation adds additional qedges and/or kedges and/or result edge bindings."""

    id: Literal["overlay"]
    parameters: dict[str, SkipValidation[JsonValue]]


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OverlayComputeJaccardParameters(OperationParameters):
    """Parameters for the OverlayComputeJaccard operation."""

    intermediate_node_key: Annotated[QNodeID, Field(examples=["n1"])]
    """A qnode key specifying the intermediate node."""

    end_node_keys: Annotated[list[QNodeID], Field(examples=["[n0, n2]"])]
    """A list of qnode keys specifying the ending nodes."""

    virtual_relation_label: Annotated[QEdgeID, Field(examples=["J1"])]
    """The key of the query graph edge that corresponds to the knowledge graph edges that were added by this operation."""


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationOverlayComputeJaccard(WorkflowOperation):
    """This operation computes the Jaccard Similarity which measures how many intermediate_node_key nodes are directly connected to both the end_node_keys nodes for all pairs of nodes with corresponding keys.

    It will then add edges to the knowledge graph along with edge attributes (with the
    property name jaccard_index) between each start_node_key and object_node_key. A
    query graph edge will also be added using the key specified by
    virtual_relation_label. This is used for purposes such as "find me all drugs
    (start_node_key) that have many proteins (intermediate_node_key) in common with
    this disease (end_node_key)." This can be used for downstream filtering to
    concentrate on relevant bioentities.
    """

    id: Literal["overlay_compute_jaccard"]
    parameters: OverlayComputeJaccardParameters


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OverlayComputeNgdParameters(OperationParameters):
    """Parameters for the OverlayComputeNgd operation."""

    virtual_relation_label: Annotated[str, Field(examples=["NGD1"])]
    """An label to help identify the virtual edge in the relation field."""

    qnode_keys: Annotated[list[QNodeID], Field(examples=["[n00, n01]"])]
    """A list of qnode keys to overlay pairwise edges onto.

    Must be be a list of at least 2 valid qnodes.
    """


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationOverlayComputeNgd(WorkflowOperation):
    """This operation computes the normalized Google distance (co-occurrence frequency) in PubMed abstracts and adds virual edges between qnodes AND/OR knodes AND/OR results edge bindings.

    If no publications are found infinity is returned.
    """

    id: Literal["overlay_compute_ngd"]
    parameters: OverlayComputeNgdParameters


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationOverlayConnectKnodes(WorkflowOperation):
    """Given a TRAPI message, create new kedges between existing knodes.

    These may be created using arbitrary methods or data sources, though provenance
    should be attached to the new kedges. Each new kedge is also added to all results
    containing node bindings to both the subject and object knodes.  This may be
    independent of any qedge connections, i.e. kedges can be created between any nodes
    in the kgraph.
    """

    id: Literal["overlay_connect_knodes"]
    parameters: dict[str, SkipValidation[JsonValue]]


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OverlayFisherExactTestParameters(OperationParameters):
    """Parameters for the OverlayFisherExactTest operation."""

    subject_qnode_key: Annotated[QNodeID, Field(examples=["n1"])]
    """A specific subject query node id."""

    object_qnode_key: Annotated[QNodeID, Field(examples=["n2"])]
    """A specific object query node id."""

    virtual_relation_label: Annotated[str, Field(examples=["f1"])]
    """An label to help identify the virtual edge."""

    rel_edge_key: Annotated[QEdgeID | None, Field(examples=["e01"])]
    """A specific Qedge id connected to both subject nodes and object nodes in message KG (optional, otherwise all edges connected to both subject nodes and object nodes in message KG are considered)."""


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationOverlayFisherExactTest(WorkflowOperation):
    """Fisher exact test computes the Fisher's Exact Test p-values of the connection between a list of given nodes with specified query id (subject_qnode_key e.g. n01) to their adjacent nodes with specified query id (object_qnode_key e.g. n02) in the message knowledge graph.

    This information is then added as an edge attribute to a virtual edge which is then
    added to the query graph and knowledge graph. It can also allow you to filter out
    the user-defined insignificance of connections based on a specified p-value cutoff
    or return the top n smallest p-value of connections and only add their corresponding
    virtual edges to the knowledge graph.
    """

    id: Literal["overlay_fisher_exact_test"]
    parameters: OverlayFisherExactTestParameters


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationRestate(WorkflowOperation):
    """This operation modifies the query graph."""

    id: Literal["restate"]
    parameters: dict[str, SkipValidation[JsonValue]]

    @property
    @override
    def unique(self) -> bool:
        """Asserts operation may produce different results depending on the agent."""
        return True


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationScore(WorkflowOperation):
    """This operation adds scores to results."""

    id: Literal["score"]
    parameters: dict[str, SkipValidation[JsonValue]]

    @property
    @override
    def unique(self) -> bool:
        """Asserts operation may produce different results depending on the agent."""
        return True


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationSortResults(WorkflowOperation):
    """This operation allows the TRAPI server to sort the elements of the list of results."""

    id: Literal["sort_results"]
    parameters: dict[str, SkipValidation[JsonValue]]


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class SortResultsEdgeAttributeParameters(OperationParameters):
    """Parameters for the SortResultsEdgeAttribute operation."""

    edge_attribute: Annotated[str, Field(examples=["normalized_google_distance"])]
    """The name of the edge attribute to order by."""

    ascending_or_descending: AscendingOrDescendingValue

    qedge_keys: Annotated[list[QEdgeID], Field(examples=["[e01]"])]
    """This indicates if you only want to consider edges with specific edge_keys.

    If not provided or empty, all edges will be looked at.
    """


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationSortResultsEdgeAttribute(WorkflowOperation):
    """This operation sorts the results by the given edge attribute.

    If in ascending order, the minimum value of the results edges with the given
    attribute will be taken while the maximum will be taken for descending order. If a
    result has no edges with the given attribute, it will be listed last. If
    `max_results` is given, it truncates the results to at most the given value.
    """

    id: Literal["sort_results_edge_attribute"]
    parameters: SortResultsEdgeAttributeParameters


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class SortResultNodeAttributeParameters(OperationParameters):
    """Parameters for the SortResultNodeAttribute operation."""

    node_attribute: Annotated[str, Field(examples=["normalized_google_distance"])]
    """The name of the node attribute to order by."""

    ascending_or_descending: AscendingOrDescendingValue

    qnode_keys: Annotated[list[QNodeID] | None, Field(examples=["[e01]"])]
    """This indicates if you only want to consider nodes with specific node_keys.

    If not provided or empty, all nodes will be looked at.
    """

    @property
    def qnode_keys_list(self) -> list[QNodeID]:
        """Return a guaranteed list of qnode_keys, empty if it is not defined."""
        return self.qnode_keys if self.qnode_keys is not None else []


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationSortResultsNodeAttribute(WorkflowOperation):
    """This operation sorts the results by the given node attribute.

    If in ascending order, the minimum value of the results nodes with the given
    attribute will be taken while the maximum will be taken for descending order. If a
    result has no nodes with the given attribute, it will be listed last. If
    `max_results` is given, it truncates the results to at most the given value.
    """

    id: Literal["sort_results_node_attribute"]
    parameters: SortResultNodeAttributeParameters


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class SortResultsScoreParameters(OperationParameters):
    """Parameters for the SortResultsScore operation."""

    ascending_or_descending: AscendingOrDescendingValue


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class OperationSortResultsScore(WorkflowOperation):
    """This operation sorts the results by the result score.

    If `max_results` is given, it truncates the results to at most the given value.
    """

    id: Literal["sort_results_score"]
    parameters: SortResultsScoreParameters
