from __future__ import annotations

from enum import Enum
from typing import Any, NewType, NotRequired, TypedDict


class SetInterpretationEnum(str, Enum):
    """Enumeration for set interpretation."""

    BATCH = "BATCH"
    ALL = "ALL"
    MANY = "MANY"


class Parameters(TypedDict):
    """Query Parameters."""

    tiers: NotRequired[list[int]]
    timeout: NotRequired[float]


class Query(TypedDict):
    """Query."""

    message: Message
    log_level: NotRequired[LogLevel | None]
    workflow: NotRequired[list[dict[str, Any]] | None]
    submitter: NotRequired[str | None]
    bypass_cache: NotRequired[bool]


class AsyncQuery(Query):
    """AsyncQuery."""

    callback: URL


class AsyncQueryResponse(TypedDict):
    """AsyncQueryResponse."""

    status: NotRequired[str | None]
    description: NotRequired[str | None]
    job_id: str


class AsyncQueryStatusResponse(TypedDict):
    """AsyncQueryStatus."""

    status: str
    description: str
    logs: list[LogEntry]
    response_url: NotRequired[URL | None]


class Response(TypedDict):
    """Response."""

    message: Message
    status: NotRequired[str | None]
    description: NotRequired[str | None]
    logs: NotRequired[list[LogEntry]]
    workflow: NotRequired[list[dict[str, Any]] | None]
    parameters: NotRequired[Parameters | None]
    schema_version: NotRequired[str | None]
    biolink_version: NotRequired[str | None]


class Message(TypedDict):
    """Message."""

    results: NotRequired[list[Result] | None]
    query_graph: NotRequired[QueryGraph | PathfinderQueryGraph | None]
    knowledge_graph: NotRequired[KnowledgeGraph | None]
    auxiliary_graphs: NotRequired[dict[AuxGraphID, AuxiliaryGraph] | None]


class LogEntry(TypedDict):
    """LogEntry."""

    timestamp: str
    level: NotRequired[LogLevel | None]
    code: NotRequired[str | None]
    message: str


class LogLevel(str, Enum):
    """Log level."""

    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


class Result(TypedDict):
    """Result."""

    node_bindings: dict[QNodeID, list[NodeBinding]]
    analyses: list[Analysis | PathfinderAnalysis]


class NodeBinding(TypedDict):
    """NodeBinding."""

    id: CURIE
    query_id: NotRequired[QNodeID | None]
    attributes: list[Attribute]


class BaseAnalysis(TypedDict):
    """Base Analysis, shared by Analysis and PathfinderAnalysis."""

    resource_id: Infores
    score: NotRequired[float | None]
    support_graphs: NotRequired[list[AuxGraphID] | None]
    scoring_method: NotRequired[str | None]
    attributes: NotRequired[list[Attribute] | None]


class Analysis(BaseAnalysis):
    """Analysis."""

    edge_bindings: dict[QEdgeID, list[EdgeBinding]]


class PathfinderAnalysis(BaseAnalysis):
    """PathfinderAnalysis."""

    path_bindings: dict[QPathID, list[PathBinding]]


class EdgeBinding(TypedDict):
    """EdgeBinding."""

    id: EdgeIdentifier
    attributes: list[Attribute]


class PathBinding(TypedDict):
    """PathBinding."""

    id: AuxGraphID


class AuxiliaryGraph(TypedDict):
    """AuxiliaryGraph."""

    edges: list[EdgeIdentifier]
    attributes: list[Attribute]


class KnowledgeGraph(TypedDict):
    """KnowledgeGraph."""

    nodes: dict[CURIE, Node]
    edges: dict[EdgeIdentifier, Edge]


class BaseQueryGraph(TypedDict):
    """QueryGraph."""

    nodes: dict[QNodeID, QNode]


class QueryGraph(BaseQueryGraph):
    edges: NotRequired[dict[QEdgeID, QEdge] | None]


class PathfinderQueryGraph(TypedDict):
    paths: dict[QPathID, QPath]


class QNode(TypedDict):
    """QNode."""

    ids: NotRequired[list[CURIE] | None]
    categories: NotRequired[list[BiolinkEntity] | None]
    set_interpretation: NotRequired[SetInterpretationEnum | None]
    member_ids: NotRequired[list[CURIE] | None]
    constraints: NotRequired[list[AttributeConstraint] | None]


class QEdge(TypedDict):
    """QEdge."""

    knowledge_type: NotRequired[str | None]
    predicates: NotRequired[list[BiolinkPredicate] | None]
    subject: CURIE
    object: CURIE
    attribute_constraints: NotRequired[list[AttributeConstraint]]
    qualifier_constraints: NotRequired[list[QualifierConstraint]]


class QPath(TypedDict):
    """QPath."""

    subject: CURIE
    object: CURIE
    predicates: NotRequired[list[BiolinkPredicate] | None]
    constraints: NotRequired[list[PathConstraint] | None]


class PathConstraint(TypedDict):
    intermediate_categories: NotRequired[list[BiolinkEntity] | None]


class Node(TypedDict):
    """Node."""

    name: NotRequired[str | None]
    categories: list[BiolinkEntity]
    attributes: list[Attribute]
    is_set: NotRequired[bool | None]


class Attribute(TypedDict):
    """Attribute."""

    attribute_type_id: str
    original_attribute_name: NotRequired[str | None]
    value: Any
    value_type_id: NotRequired[str | None]
    attribute_source: NotRequired[str | None]
    value_url: NotRequired[URL | None]
    attributes: NotRequired[list[Attribute] | None]


class Edge(TypedDict):
    """Edge."""

    predicate: BiolinkPredicate
    subject: CURIE
    object: CURIE
    attributes: NotRequired[list[Attribute] | None]
    qualifiers: NotRequired[list[Qualifier] | None]
    sources: list[RetrievalSource]


class Qualifier(TypedDict):
    """Qualifier."""

    qualifier_type_id: QualifierTypeID
    qualifier_value: str


class QualifierConstraint(TypedDict):
    """QualifierConstraint."""

    qualifier_set: list[Qualifier]


BiolinkEntity = NewType("BiolinkEntity", str)
BiolinkPredicate = NewType("BiolinkPredicate", str)
CURIE = NewType("CURIE", str)


class MetaKnowledgeGraph(TypedDict):
    """MetaKnowledgeGraph."""

    nodes: dict[BiolinkEntity, MetaNode]
    edges: list[MetaEdge]


class MetaNode(TypedDict):
    """MetaNode."""

    id_prefixes: list[str]
    attributes: NotRequired[list[MetaAttribute] | None]


class MetaEdge(TypedDict):
    """MetaEdge."""

    subject: BiolinkEntity
    predicate: BiolinkPredicate
    object: BiolinkEntity
    knowledge_types: NotRequired[list[str] | None]
    attributes: NotRequired[list[MetaAttribute] | None]
    qualifiers: NotRequired[list[MetaQualifier] | None]


class MetaQualifier(TypedDict):
    """MetaQualifier."""

    qualifier_type_id: QualifierTypeID
    applicable_values: NotRequired[list[str]]


class MetaAttribute(TypedDict):
    """MetaAttribute."""

    attribute_type_id: str
    attribute_source: NotRequired[str | None]
    original_attribute_names: NotRequired[list[str] | None]
    constraint_use: NotRequired[bool]
    constraint_name: NotRequired[str | None]


# AttributeConstraint
AttributeConstraint = TypedDict(
    "AttributeConstraint",
    {
        "id": str,
        "name": str,
        "not": NotRequired[bool],
        "operator": str,
        "value": Any,
        "unit_id": NotRequired[str | None],
        "unit_name": NotRequired[str | None],
    },
)


class RetrievalSource(TypedDict):
    """RetrievalSource."""

    resource_id: Infores
    resource_role: str
    upstream_resource_ids: NotRequired[list[Infores] | None]
    source_record_urls: NotRequired[list[str] | None]


# These don't offer any special behavior, but make type annotation less confusable
EdgeIdentifier = NewType("EdgeIdentifier", str)
AuxGraphID = NewType("AuxGraphID", str)
QNodeID = NewType("QNodeID", str)
QEdgeID = NewType("QEdgeID", str)
QPathID = NewType("QPathID", str)
Infores = NewType("Infores", str)
QualifierTypeID = NewType("QualifierTypeID", str)
URL = NewType("URL", str)
