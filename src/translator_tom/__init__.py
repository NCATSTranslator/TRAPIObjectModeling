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
]

from translator_tom.models.analysis import (
    Analysis,
    BaseAnalysis,
    PathfinderAnalysis,
)
from translator_tom.models.asyncquery import (
    AsyncQuery,
    AsyncQueryResponse,
    AsyncQueryStatusResponse,
)
from translator_tom.models.attribute import (
    Attribute,
    AttributeConstraint,
    OperatorEnum,
)
from translator_tom.models.auxiliary_graph import AuxiliaryGraph
from translator_tom.models.edge_binding import EdgeBinding
from translator_tom.models.knowledge_graph import Edge, KnowledgeGraph, Node
from translator_tom.models.log_entry import LogEntry, LogLevel
from translator_tom.models.message import Message
from translator_tom.models.meta_attribute import MetaAttribute
from translator_tom.models.meta_knowledge_graph import (
    MetaEdge,
    MetaKnowledgeGraph,
    MetaNode,
)
from translator_tom.models.meta_qualifier import MetaQualifier
from translator_tom.models.node_binding import NodeBinding
from translator_tom.models.path_binding import PathBinding
from translator_tom.models.path_constraint import PathConstraint
from translator_tom.models.qualifier import Qualifier, QualifierConstraint
from translator_tom.models.query import Query
from translator_tom.models.query_graph import (
    BaseQueryGraph,
    PathfinderQueryGraph,
    QEdge,
    QNode,
    QPath,
    QueryGraph,
    SetInterpetationEnum,
)
from translator_tom.models.response import Response
from translator_tom.models.result import Result
from translator_tom.models.retrieval_source import (
    ResourceRoleEnum,
    RetrievalSource,
)
from translator_tom.models.shared import (
    Curie,
    KnowledgeTypeEnum,
    biolink,
    infores,
)
from translator_tom.models.workflow_operations import (
    AboveOrBelowEnum,
    AllowList,
    AscendingOrDescending,
    DenyList,
    OperationParameters,
    PlusOrMinusEnum,
    TopOrBottomEnum,
    WorkflowOperation,
)
from translator_tom.utils.object_base import TOMBaseObject


# Eagerly build TypeAdapters for all models at import time, prevents cold-start overhead
def _build_all_adapters() -> None:
    """Walk subclass tree and build TypeAdapters eagerly."""
    queue: list[type[TOMBaseObject]] = list(TOMBaseObject.__subclasses__())
    while queue:
        cls = queue.pop()
        cls.get_type_adapter()
        queue.extend(cls.__subclasses__())


_build_all_adapters()
