from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, NewType
from dataclasses_json import config

from pydantic import BaseModel


class SetInterpretationEnum(str, Enum):
    """Enumeration for set interpretation."""

    BATCH = "BATCH"
    ALL = "ALL"
    MANY = "MANY"


class Parameters(BaseModel):
    """Query Parameters."""

    tiers: list[int] | None = None
    timeout: float | None = None


class Query(BaseModel):
    """Query."""

    message: Message
    log_level: LogLevel | None = None
    workflow: list[Any] | None | None = None
    submitter: str | None = None
    bypass_cache: bool | None = None


class AsyncQuery(Query):
    """AsyncQuery."""

    callback: URL


class AsyncQueryResponse(BaseModel):
    """AsyncQueryResponse."""

    status: str | None = None
    description: str | None = None
    job_id: str


class AsyncQueryStatusResponse(BaseModel):
    """AsyncQueryStatus."""

    status: str
    description: str
    logs: list[LogEntry]
    response_url: URL | None = None


class Response(BaseModel):
    """Response."""

    message: Message
    status: str | None = None
    description: str | None = None
    logs: list[LogEntry] | None = None
    workflow: list[dict[str, Any]] | None | None = None
    parameters: Parameters | None = None
    schema_version: str | None = None
    biolink_version: str | None = None


class Message(BaseModel):
    """Message."""

    results: list[Result] | None | None = None
    query_graph: QueryGraph | PathfinderQueryGraph | None = None
    knowledge_graph: KnowledgeGraph | None = None
    auxiliary_graphs: dict[AuxGraphID, AuxiliaryGraph] | None | None = None


class LogEntry(BaseModel):
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


class Result(BaseModel):
    """Result."""

    node_bindings: dict[QNodeID, list[NodeBinding]]
    analyses: list[Analysis | PathfinderAnalysis]


class NodeBinding(BaseModel):
    """NodeBinding."""

    id: CURIE
    query_id: QNodeID | None = None
    attributes: list[Attribute]


class BaseAnalysis(BaseModel):
    """Base Analysis, shared by Analysis and PathfinderAnalysis."""

    resource_id: Infores
    score: float | None = None
    support_graphs: list[AuxGraphID] | None | None = None
    scoring_method: str | None = None
    attributes: list[Attribute] | None | None = None


class Analysis(BaseAnalysis):
    """Analysis."""

    edge_bindings: dict[QEdgeID, list[EdgeBinding]]


class PathfinderAnalysis(BaseAnalysis):
    """PathfinderAnalysis."""

    path_bindings: dict[QPathID, list[PathBinding]]


class EdgeBinding(BaseModel):
    """EdgeBinding."""

    id: EdgeIdentifier
    attributes: list[Attribute]


class PathBinding(BaseModel):
    """PathBinding."""

    id: AuxGraphID


class AuxiliaryGraph(BaseModel):
    """AuxiliaryGraph."""

    edges: list[EdgeIdentifier]
    attributes: list[Attribute]


class KnowledgeGraph(BaseModel):
    """KnowledgeGraph."""

    nodes: dict[CURIE, Node]
    edges: dict[EdgeIdentifier, Edge]


class BaseQueryGraph(BaseModel):
    """QueryGraph."""

    nodes: dict[QNodeID, QNode]


class QueryGraph(BaseQueryGraph):
    edges: dict[QEdgeID, QEdge] | None | None = None


class PathfinderQueryGraph(BaseModel):
    paths: dict[QPathID, QPath]


class QNode(BaseModel):
    """QNode."""

    ids: list[CURIE] | None | None = None
    categories: list[BiolinkEntity] | None | None = None
    set_interpretation: SetInterpretationEnum | None = None
    member_ids: list[CURIE] | None | None = None
    constraints: list[AttributeConstraint] | None | None = None


class QEdge(BaseModel):
    """QEdge."""

    knowledge_type: str | None = None
    predicates: list[BiolinkPredicate] | None | None = None
    subject: CURIE
    object: CURIE
    attribute_constraints: list[AttributeConstraint] | None = None
    qualifier_constraints: list[QualifierConstraint] | None = None


class QPath(BaseModel):
    """QPath."""

    subject: CURIE
    object: CURIE
    predicates: list[BiolinkPredicate] | None | None = None
    constraints: list[PathConstraint] | None | None = None


class PathConstraint(BaseModel):
    intermediate_categories: list[BiolinkEntity] | None | None = None


class Node(BaseModel):
    """Node."""

    name: str | None = None
    categories: list[BiolinkEntity]
    attributes: list[Attribute]
    is_set: bool | None = None


class Attribute(BaseModel):
    """Attribute."""

    attribute_type_id: str
    original_attribute_name: str | None = None
    value: Any
    value_type_id: str | None = None
    attribute_source: str | None = None
    value_url: URL | None = None
    attributes: list[Attribute] | None | None = None


class Edge(BaseModel):
    """Edge."""

    predicate: BiolinkPredicate
    subject: CURIE
    object: CURIE
    attributes: list[Attribute] | None | None = None
    qualifiers: list[Qualifier] | None | None = None
    sources: list[RetrievalSource]


class Qualifier(BaseModel):
    """Qualifier."""

    qualifier_type_id: QualifierTypeID
    qualifier_value: str


class QualifierConstraint(BaseModel):
    """QualifierConstraint."""

    qualifier_set: list[Qualifier]


BiolinkEntity = NewType("BiolinkEntity", str)
BiolinkPredicate = NewType("BiolinkPredicate", str)
CURIE = NewType("CURIE", str)


class MetaKnowledgeGraph(BaseModel):
    """MetaKnowledgeGraph."""

    nodes: dict[BiolinkEntity, MetaNode]
    edges: list[MetaEdge]


class MetaNode(BaseModel):
    """MetaNode."""

    id_prefixes: list[str]
    attributes: list[MetaAttribute] | None | None = None


class MetaEdge(BaseModel):
    """MetaEdge."""

    subject: BiolinkEntity
    predicate: BiolinkPredicate
    object: BiolinkEntity
    knowledge_types: list[str] | None | None = None
    attributes: list[MetaAttribute] | None | None = None
    qualifiers: list[MetaQualifier] | None | None = None


class MetaQualifier(BaseModel):
    """MetaQualifier."""

    qualifier_type_id: QualifierTypeID
    applicable_values: list[str] | None = None


class MetaAttribute(BaseModel):
    """MetaAttribute."""

    attribute_type_id: str
    attribute_source: str | None = None
    original_attribute_names: list[str] | None | None = None
    constraint_use: bool | None = None
    constraint_name: str | None = None


class AttributeConstraint(BaseModel):
    """AttributeConstraint."""

    id: str
    name: str
    not_condition: bool | None = field(default=None, metadata=config(field_name="not"))
    operator: str
    value: Any
    unit_id: str | None = None
    unit_name: str | None = None


class RetrievalSource(BaseModel):
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
