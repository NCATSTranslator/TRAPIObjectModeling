"""TRAPI Object Modeling."""

__all__ = [
    "AboveOrBelowEnum",
    "AllowList",
    "Analysis",
    "AscendingOrDescending",
    "AsyncQuery",
    "AsyncQueryResponse",
    "AsyncQueryStatusResponse",
    "Attribute",
    "AttributeConstraint",
    "AuxiliaryGraph",
    "BaseAnalysis",
    "BaseQueryGraph",
    "Curie",
    "DenyList",
    "Edge",
    "EdgeBinding",
    "KnowledgeGraph",
    "KnowledgeTypeEnum",
    "LogEntry",
    "LogLevel",
    "Message",
    "MetaAttribute",
    "MetaEdge",
    "MetaKnowledgeGraph",
    "MetaNode",
    "MetaQualifier",
    "Node",
    "NodeBinding",
    "OperationParameters",
    "OperatorEnum",
    "PathBinding",
    "PathConstraint",
    "PathfinderAnalysis",
    "PathfinderQueryGraph",
    "PlusOrMinusEnum",
    "QEdge",
    "QNode",
    "QPath",
    "Qualifier",
    "QualifierConstraint",
    "Query",
    "QueryGraph",
    "ResourceRoleEnum",
    "Response",
    "Result",
    "RetrievalSource",
    "SetInterpetationEnum",
    "TOMBaseObject",
    "TopOrBottomEnum",
    "WorkflowOperation",
    "biolink",
    "infores",
    "passes_semantic_validation",
    "semantic_validate",
]

from trapi_object_modeling.models.analysis import (
    Analysis,
    BaseAnalysis,
    PathfinderAnalysis,
)
from trapi_object_modeling.models.asyncquery import (
    AsyncQuery,
    AsyncQueryResponse,
    AsyncQueryStatusResponse,
)
from trapi_object_modeling.models.attribute import Attribute
from trapi_object_modeling.models.attribute_constraint import (
    AttributeConstraint,
    OperatorEnum,
)
from trapi_object_modeling.models.auxiliary_graph import AuxiliaryGraph
from trapi_object_modeling.models.edge_binding import EdgeBinding
from trapi_object_modeling.models.knowledge_graph import Edge, KnowledgeGraph, Node
from trapi_object_modeling.models.log_entry import LogEntry, LogLevel
from trapi_object_modeling.models.message import Message
from trapi_object_modeling.models.meta_attribute import MetaAttribute
from trapi_object_modeling.models.meta_knowledge_graph import (
    MetaEdge,
    MetaKnowledgeGraph,
    MetaNode,
)
from trapi_object_modeling.models.meta_qualifier import MetaQualifier
from trapi_object_modeling.models.node_binding import NodeBinding
from trapi_object_modeling.models.path_binding import PathBinding
from trapi_object_modeling.models.path_constraint import PathConstraint
from trapi_object_modeling.models.qualifier import Qualifier
from trapi_object_modeling.models.qualifier_constraint import QualifierConstraint
from trapi_object_modeling.models.query import Query
from trapi_object_modeling.models.query_graph import (
    BaseQueryGraph,
    PathfinderQueryGraph,
    QEdge,
    QNode,
    QPath,
    QueryGraph,
    SetInterpetationEnum,
)
from trapi_object_modeling.models.response import Response
from trapi_object_modeling.models.result import Result
from trapi_object_modeling.models.retrieval_source import (
    ResourceRoleEnum,
    RetrievalSource,
)
from trapi_object_modeling.models.shared import (
    Curie,
    KnowledgeTypeEnum,
    biolink,
    infores,
)
from trapi_object_modeling.models.workflow_operations import (
    AboveOrBelowEnum,
    AllowList,
    AscendingOrDescending,
    DenyList,
    OperationParameters,
    PlusOrMinusEnum,
    TopOrBottomEnum,
    WorkflowOperation,
)
from trapi_object_modeling.utils.object_base import TOMBaseObject
from trapi_object_modeling.validation import (
    passes_semantic_validation,
    semantic_validate,
)


# Eagerly build TypeAdapters for all models at import time, prevents cold-start overhead
def _build_all_adapters() -> None:
    """Walk subclass tree and build TypeAdapters eagerly."""
    queue: list[type[TOMBaseObject]] = list(TOMBaseObject.__subclasses__())
    while queue:
        cls = queue.pop()
        cls.get_type_adapter()
        queue.extend(cls.__subclasses__())


_build_all_adapters()
