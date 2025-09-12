from __future__ import annotations

from enum import Enum
from typing import Any, NewType
from pydantic import Field
from pydantic.dataclasses import dataclass


class SetInterpretationEnum(str, Enum):
    """Enumeration for set interpretation."""

    BATCH = "BATCH"
    ALL = "ALL"
    MANY = "MANY"


@dataclass(kw_only=True)
class Parameters:
    """Query Parameters."""

    tiers: list[int] | None = None
    timeout: float | None = None


@dataclass(kw_only=True)
class Query:
    """Query."""

    message: Message
    log_level: LogLevel | None = None
    workflow: list[Any] | None | None = None
    submitter: str | None = None
    bypass_cache: bool | None = None


@dataclass(kw_only=True)
class AsyncQuery(Query):
    """AsyncQuery."""

    callback: URL


@dataclass(kw_only=True)
class AsyncQueryResponse:
    """AsyncQueryResponse."""

    status: str | None = None
    description: str | None = None
    job_id: str


@dataclass(kw_only=True)
class AsyncQueryStatusResponse:
    """AsyncQueryStatus."""

    status: str
    description: str
    logs: list[LogEntry]
    response_url: URL | None = None


@dataclass(kw_only=True)
class Response:
    """Response."""

    message: Message
    status: str | None = None
    description: str | None = None
    logs: list[LogEntry] | None = None
    workflow: list[dict[str, Any]] | None | None = None
    parameters: Parameters | None = None
    schema_version: str | None = None
    biolink_version: str | None = None


@dataclass(kw_only=True)
class Message:
    """Message."""

    results: list[Result] | None | None = None
    query_graph: QueryGraph | PathfinderQueryGraph | None = None
    knowledge_graph: KnowledgeGraph | None = None
    auxiliary_graphs: dict[AuxGraphID, AuxiliaryGraph] | None | None = None


@dataclass(kw_only=True)
class LogEntry:
    """LogEntry."""

    timestamp: str
    level: LogLevel | None = None
    code: str | None = None
    message: str


class LogLevel(str, Enum):
    """Log level."""

    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


@dataclass(kw_only=True)
class Result:
    """Result."""

    node_bindings: dict[QNodeID, list[NodeBinding]]
    analyses: list[Analysis | PathfinderAnalysis]


@dataclass(kw_only=True)
class NodeBinding:
    """NodeBinding."""

    id: CURIE
    query_id: QNodeID | None = None
    attributes: list[Attribute]


@dataclass(kw_only=True)
class BaseAnalysis:
    """Base Analysis, shared by Analysis and PathfinderAnalysis."""

    resource_id: Infores
    score: float | None = None
    support_graphs: list[AuxGraphID] | None | None = None
    scoring_method: str | None = None
    attributes: list[Attribute] | None | None = None


@dataclass(kw_only=True)
class Analysis(BaseAnalysis):
    """Analysis."""

    edge_bindings: dict[QEdgeID, list[EdgeBinding]]


@dataclass(kw_only=True)
class PathfinderAnalysis(BaseAnalysis):
    """PathfinderAnalysis."""

    path_bindings: dict[QPathID, list[PathBinding]]


@dataclass(kw_only=True)
class EdgeBinding:
    """EdgeBinding."""

    id: EdgeIdentifier
    attributes: list[Attribute]


@dataclass(kw_only=True)
class PathBinding:
    """PathBinding."""

    id: AuxGraphID


@dataclass(kw_only=True)
class AuxiliaryGraph:
    """AuxiliaryGraph."""

    edges: list[EdgeIdentifier]
    attributes: list[Attribute]


@dataclass(kw_only=True)
class KnowledgeGraph:
    """KnowledgeGraph."""

    nodes: dict[CURIE, Node]
    edges: dict[EdgeIdentifier, Edge]


@dataclass(kw_only=True)
class BaseQueryGraph:
    """QueryGraph."""

    nodes: dict[QNodeID, QNode]


class QueryGraph(BaseQueryGraph):
    edges: dict[QEdgeID, QEdge] | None | None = None


@dataclass(kw_only=True)
class PathfinderQueryGraph:
    paths: dict[QPathID, QPath]


@dataclass(kw_only=True)
class QNode:
    """QNode."""

    ids: list[CURIE] | None | None = None
    categories: list[BiolinkEntity] | None | None = None
    set_interpretation: SetInterpretationEnum | None = None
    member_ids: list[CURIE] | None | None = None
    constraints: list[AttributeConstraint] | None | None = None


@dataclass(kw_only=True)
class QEdge:
    """QEdge."""

    knowledge_type: str | None = None
    predicates: list[BiolinkPredicate] | None | None = None
    subject: CURIE
    object: CURIE
    attribute_constraints: list[AttributeConstraint] | None = None
    qualifier_constraints: list[QualifierConstraint] | None = None


@dataclass(kw_only=True)
class QPath:
    """QPath."""

    subject: CURIE
    object: CURIE
    predicates: list[BiolinkPredicate] | None | None = None
    constraints: list[PathConstraint] | None | None = None


@dataclass(kw_only=True)
class PathConstraint:
    intermediate_categories: list[BiolinkEntity] | None | None = None


@dataclass(kw_only=True)
class Node:
    """Node."""

    name: str | None = None
    categories: list[BiolinkEntity]
    attributes: list[Attribute]
    is_set: bool | None = None


@dataclass(kw_only=True)
class Attribute:
    """Attribute."""

    attribute_type_id: str
    original_attribute_name: str | None = None
    value: Any
    value_type_id: str | None = None
    attribute_source: str | None = None
    value_url: URL | None = None
    attributes: list[Attribute] | None | None = None


@dataclass(kw_only=True)
class Edge:
    """Edge."""

    predicate: BiolinkPredicate
    subject: CURIE
    object: CURIE
    attributes: list[Attribute] | None | None = None
    qualifiers: list[Qualifier] | None | None = None
    sources: list[RetrievalSource]


@dataclass(kw_only=True)
class Qualifier:
    """Qualifier."""

    qualifier_type_id: QualifierTypeID
    qualifier_value: str


@dataclass(kw_only=True)
class QualifierConstraint:
    """QualifierConstraint."""

    qualifier_set: list[Qualifier]


BiolinkEntity = NewType("BiolinkEntity", str)
BiolinkPredicate = NewType("BiolinkPredicate", str)
CURIE = NewType("CURIE", str)


@dataclass(kw_only=True)
class MetaKnowledgeGraph:
    """MetaKnowledgeGraph."""

    nodes: dict[BiolinkEntity, MetaNode]
    edges: list[MetaEdge]


@dataclass(kw_only=True)
class MetaNode:
    """MetaNode."""

    id_prefixes: list[str]
    attributes: list[MetaAttribute] | None | None = None


@dataclass(kw_only=True)
class MetaEdge:
    """MetaEdge."""

    subject: BiolinkEntity
    predicate: BiolinkPredicate
    object: BiolinkEntity
    knowledge_types: list[str] | None | None = None
    attributes: list[MetaAttribute] | None | None = None
    qualifiers: list[MetaQualifier] | None | None = None


@dataclass(kw_only=True)
class MetaQualifier:
    """MetaQualifier."""

    qualifier_type_id: QualifierTypeID
    applicable_values: list[str] | None = None


@dataclass(kw_only=True)
class MetaAttribute:
    """MetaAttribute."""

    attribute_type_id: str
    attribute_source: str | None = None
    original_attribute_names: list[str] | None | None = None
    constraint_use: bool | None = None
    constraint_name: str | None = None


@dataclass(kw_only=True)
class AttributeConstraint:
    """AttributeConstraint."""

    id: str
    name: str
    not_condition: bool | None = Field(default=None, alias="not", title="not")
    operator: str
    value: Any
    unit_id: str | None = None
    unit_name: str | None = None


@dataclass(kw_only=True)
class RetrievalSource:
    """RetrievalSource."""

    resource_id: Infores
    resource_role: str
    upstream_resource_ids: list[Infores] | None | None = None
    source_record_urls: list[str] | None | None = None


# These don't offer any special behavior, but make type annotation less confusable
EdgeIdentifier = NewType("EdgeIdentifier", str)
AuxGraphID = NewType("AuxGraphID", str)
QNodeID = NewType("QNodeID", str)
QEdgeID = NewType("QEdgeID", str)
QPathID = NewType("QPathID", str)
Infores = NewType("Infores", str)
QualifierTypeID = NewType("QualifierTypeID", str)
URL = NewType("URL", str)
