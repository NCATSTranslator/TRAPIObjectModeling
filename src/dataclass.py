from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, NewType
from dataclasses_json import config

from mashumaro import DataClassDictMixin
from mashumaro.mixins.orjson import DataClassORJSONMixin


class SetInterpretationEnum(str, Enum):
    """Enumeration for set interpretation."""

    BATCH = "BATCH"
    ALL = "ALL"
    MANY = "MANY"


@dataclass(slots=True, kw_only=True)
class Parameters(DataClassORJSONMixin, DataClassDictMixin):
    """Query Parameters."""

    tiers: list[int] | None = None
    timeout: float | None = None


@dataclass(slots=True, kw_only=True)
class Query(DataClassORJSONMixin, DataClassDictMixin):
    """Query."""

    message: Message
    log_level: LogLevel | None = None
    workflow: list[Any] | None | None = None
    submitter: str | None = None
    bypass_cache: bool | None = None


@dataclass(slots=True, kw_only=True)
class AsyncQuery(Query):
    """AsyncQuery."""

    callback: URL


@dataclass(slots=True, kw_only=True)
class AsyncQueryResponse(DataClassORJSONMixin, DataClassDictMixin):
    """AsyncQueryResponse."""

    status: str | None = None
    description: str | None = None
    job_id: str


@dataclass(slots=True, kw_only=True)
class AsyncQueryStatusResponse(DataClassORJSONMixin, DataClassDictMixin):
    """AsyncQueryStatus."""

    status: str
    description: str
    logs: list[LogEntry]
    response_url: URL | None = None


@dataclass(slots=True, kw_only=True)
class Response(DataClassORJSONMixin, DataClassDictMixin):
    """Response."""

    message: Message
    status: str | None = None
    description: str | None = None
    logs: list[LogEntry] | None = None
    workflow: list[dict[str, Any]] | None | None = None
    parameters: Parameters | None = None
    schema_version: str | None = None
    biolink_version: str | None = None


@dataclass(slots=True, kw_only=True)
class Message(DataClassORJSONMixin, DataClassDictMixin):
    """Message."""

    results: list[Result] | None | None = None
    query_graph: QueryGraph | PathfinderQueryGraph | None = None
    knowledge_graph: KnowledgeGraph | None = None
    auxiliary_graphs: dict[AuxGraphID, AuxiliaryGraph] | None | None = None


@dataclass(slots=True, kw_only=True)
class LogEntry(DataClassORJSONMixin, DataClassDictMixin):
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


@dataclass(slots=True, kw_only=True)
class Result(DataClassORJSONMixin, DataClassDictMixin):
    """Result."""

    node_bindings: dict[QNodeID, list[NodeBinding]]
    analyses: list[Analysis | PathfinderAnalysis]


@dataclass(slots=True, kw_only=True)
class NodeBinding(DataClassORJSONMixin, DataClassDictMixin):
    """NodeBinding."""

    id: CURIE
    query_id: QNodeID | None = None
    attributes: list[Attribute]


@dataclass(slots=True, kw_only=True)
class BaseAnalysis(DataClassORJSONMixin, DataClassDictMixin):
    """Base Analysis, shared by Analysis and PathfinderAnalysis."""

    resource_id: Infores
    score: float | None = None
    support_graphs: list[AuxGraphID] | None | None = None
    scoring_method: str | None = None
    attributes: list[Attribute] | None | None = None


@dataclass(slots=True, kw_only=True)
class Analysis(BaseAnalysis):
    """Analysis."""

    edge_bindings: dict[QEdgeID, list[EdgeBinding]]


@dataclass(slots=True, kw_only=True)
class PathfinderAnalysis(BaseAnalysis):
    """PathfinderAnalysis."""

    path_bindings: dict[QPathID, list[PathBinding]]


@dataclass(slots=True, kw_only=True)
class EdgeBinding(DataClassORJSONMixin, DataClassDictMixin):
    """EdgeBinding."""

    id: EdgeIdentifier
    attributes: list[Attribute]


@dataclass(slots=True, kw_only=True)
class PathBinding(DataClassORJSONMixin, DataClassDictMixin):
    """PathBinding."""

    id: AuxGraphID


@dataclass(slots=True, kw_only=True)
class AuxiliaryGraph(DataClassORJSONMixin, DataClassDictMixin):
    """AuxiliaryGraph."""

    edges: list[EdgeIdentifier]
    attributes: list[Attribute]


@dataclass(slots=True, kw_only=True)
class KnowledgeGraph(DataClassORJSONMixin, DataClassDictMixin):
    """KnowledgeGraph."""

    nodes: dict[CURIE, Node]
    edges: dict[EdgeIdentifier, Edge]


@dataclass(slots=True, kw_only=True)
class BaseQueryGraph(DataClassORJSONMixin, DataClassDictMixin):
    """QueryGraph."""

    nodes: dict[QNodeID, QNode]


class QueryGraph(BaseQueryGraph):
    edges: dict[QEdgeID, QEdge] | None | None = None


@dataclass(slots=True, kw_only=True)
class PathfinderQueryGraph(DataClassORJSONMixin, DataClassDictMixin):
    paths: dict[QPathID, QPath]


@dataclass(slots=True, kw_only=True)
class QNode(DataClassORJSONMixin, DataClassDictMixin):
    """QNode."""

    ids: list[CURIE] | None | None = None
    categories: list[BiolinkEntity] | None | None = None
    set_interpretation: SetInterpretationEnum | None = None
    member_ids: list[CURIE] | None | None = None
    constraints: list[AttributeConstraint] | None | None = None


@dataclass(slots=True, kw_only=True)
class QEdge(DataClassORJSONMixin, DataClassDictMixin):
    """QEdge."""

    knowledge_type: str | None = None
    predicates: list[BiolinkPredicate] | None | None = None
    subject: CURIE
    object: CURIE
    attribute_constraints: list[AttributeConstraint] | None = None
    qualifier_constraints: list[QualifierConstraint] | None = None


@dataclass(slots=True, kw_only=True)
class QPath(DataClassORJSONMixin, DataClassDictMixin):
    """QPath."""

    subject: CURIE
    object: CURIE
    predicates: list[BiolinkPredicate] | None | None = None
    constraints: list[PathConstraint] | None | None = None


@dataclass(slots=True, kw_only=True)
class PathConstraint(DataClassORJSONMixin, DataClassDictMixin):
    intermediate_categories: list[BiolinkEntity] | None | None = None


@dataclass(slots=True, kw_only=True)
class Node(DataClassORJSONMixin, DataClassDictMixin):
    """Node."""

    name: str | None = None
    categories: list[BiolinkEntity]
    attributes: list[Attribute]
    is_set: bool | None = None


@dataclass(slots=True, kw_only=True)
class Attribute(DataClassORJSONMixin, DataClassDictMixin):
    """Attribute."""

    attribute_type_id: str
    original_attribute_name: str | None = None
    value: Any
    value_type_id: str | None = None
    attribute_source: str | None = None
    value_url: URL | None = None
    attributes: list[Attribute] | None | None = None


@dataclass(slots=True, kw_only=True)
class Edge(DataClassORJSONMixin, DataClassDictMixin):
    """Edge."""

    predicate: BiolinkPredicate
    subject: CURIE
    object: CURIE
    attributes: list[Attribute] | None | None = None
    qualifiers: list[Qualifier] | None | None = None
    sources: list[RetrievalSource]


@dataclass(slots=True, kw_only=True)
class Qualifier(DataClassORJSONMixin, DataClassDictMixin):
    """Qualifier."""

    qualifier_type_id: QualifierTypeID
    qualifier_value: str


@dataclass(slots=True, kw_only=True)
class QualifierConstraint(DataClassORJSONMixin, DataClassDictMixin):
    """QualifierConstraint."""

    qualifier_set: list[Qualifier]


BiolinkEntity = NewType("BiolinkEntity", str)
BiolinkPredicate = NewType("BiolinkPredicate", str)
CURIE = NewType("CURIE", str)


@dataclass(slots=True, kw_only=True)
class MetaKnowledgeGraph(DataClassORJSONMixin, DataClassDictMixin):
    """MetaKnowledgeGraph."""

    nodes: dict[BiolinkEntity, MetaNode]
    edges: list[MetaEdge]


@dataclass(slots=True, kw_only=True)
class MetaNode(DataClassORJSONMixin, DataClassDictMixin):
    """MetaNode."""

    id_prefixes: list[str]
    attributes: list[MetaAttribute] | None | None = None


@dataclass(slots=True, kw_only=True)
class MetaEdge(DataClassORJSONMixin, DataClassDictMixin):
    """MetaEdge."""

    subject: BiolinkEntity
    predicate: BiolinkPredicate
    object: BiolinkEntity
    knowledge_types: list[str] | None | None = None
    attributes: list[MetaAttribute] | None | None = None
    qualifiers: list[MetaQualifier] | None | None = None


@dataclass(slots=True, kw_only=True)
class MetaQualifier(DataClassORJSONMixin, DataClassDictMixin):
    """MetaQualifier."""

    qualifier_type_id: QualifierTypeID
    applicable_values: list[str] | None = None


@dataclass(slots=True, kw_only=True)
class MetaAttribute(DataClassORJSONMixin, DataClassDictMixin):
    """MetaAttribute."""

    attribute_type_id: str
    attribute_source: str | None = None
    original_attribute_names: list[str] | None | None = None
    constraint_use: bool | None = None
    constraint_name: str | None = None


@dataclass(slots=True, kw_only=True)
class AttributeConstraint(DataClassORJSONMixin, DataClassDictMixin):
    """AttributeConstraint."""

    id: str
    name: str
    not_condition: bool | None = field(default=None, metadata=config(field_name="not"))
    operator: str
    value: Any
    unit_id: str | None = None
    unit_name: str | None = None


@dataclass(slots=True, kw_only=True)
class RetrievalSource(DataClassORJSONMixin, DataClassDictMixin):
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
