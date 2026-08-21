"""TRAPI Object Modeling."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _version

try:
    __version__ = _version("translator_tom")
except PackageNotFoundError:  # pragma: no cover - package not installed (source tree)
    __version__ = "0.0.0"

__all__ = [
    "CURIE",
    "TRAPI_CONFIG",
    "Analysis",
    "AsyncQuery",
    "AsyncQueryResponse",
    "AsyncQueryStatusResponse",
    "Attribute",
    "AttributeConstraint",
    "AuxGraphID",
    "AuxiliaryGraph",
    "AuxiliaryGraphsDict",
    "BaseAnalysis",
    "BaseQueryGraph",
    "Biolink",
    "Curie",
    "Delta",
    "DictUtil",
    "Edge",
    "EdgeBinding",
    "EdgeID",
    "FastJsonValue",
    "HashRepEnum",
    "Infores",
    "KnowledgeGraph",
    "KnowledgeType",
    "KnowledgeTypeEnum",
    "LogEntry",
    "LogLevel",
    "LogLevelEnum",
    "Message",
    "MetaAttribute",
    "MetaEdge",
    "MetaKnowledgeGraph",
    "MetaNode",
    "MetaQualifier",
    "Node",
    "NodeBinding",
    "Operation",
    "Operator",
    "OperatorEnum",
    "PathBinding",
    "PathConstraint",
    "PathfinderAnalysis",
    "PathfinderQueryGraph",
    "QEdge",
    "QEdgeID",
    "QNode",
    "QNodeID",
    "QPath",
    "QPathID",
    "Qualifier",
    "QualifierConstraint",
    "Query",
    "QueryGraph",
    "ResourceRole",
    "ResourceRoleEnum",
    "Response",
    "Result",
    "RetrievalSource",
    "SetInterpretation",
    "SetInterpretationEnum",
    "TOMBase",
    "diff",
    "infores",
    "register_union_discriminator",
    "tomhash",
    "tomhash_int",
    "tomhash_to_int",
    "workflow",
]

from translator_tom.utils.biolink import Biolink
from translator_tom.utils.config import TRAPI_CONFIG, HashRepEnum
from translator_tom.utils.dict_util_base import DictUtil, register_union_discriminator
from translator_tom.utils.hash import tomhash, tomhash_int, tomhash_to_int
from translator_tom.utils.object_base import TOMBase
from translator_tom.utils.shared import (
    CURIE,
    AuxGraphID,
    Curie,
    EdgeID,
    FastJsonValue,
    Infores,
    KnowledgeType,
    KnowledgeTypeEnum,
    QEdgeID,
    QNodeID,
    QPathID,
    infores,
)
from translator_tom.v1_6.models import workflow_operations as workflow
from translator_tom.v1_6.models.analysis import (
    Analysis,
    BaseAnalysis,
    PathfinderAnalysis,
)
from translator_tom.v1_6.models.asyncquery import (
    AsyncQuery,
    AsyncQueryResponse,
    AsyncQueryStatusResponse,
)
from translator_tom.v1_6.models.attribute import (
    Attribute,
    AttributeConstraint,
    Operator,
    OperatorEnum,
)
from translator_tom.v1_6.models.auxiliary_graph import (
    AuxiliaryGraph,
    AuxiliaryGraphsDict,
)
from translator_tom.v1_6.models.edge_binding import EdgeBinding
from translator_tom.v1_6.models.knowledge_graph import Edge, KnowledgeGraph, Node
from translator_tom.v1_6.models.log_entry import LogEntry, LogLevel, LogLevelEnum
from translator_tom.v1_6.models.message import Message
from translator_tom.v1_6.models.meta_attribute import MetaAttribute
from translator_tom.v1_6.models.meta_knowledge_graph import (
    MetaEdge,
    MetaKnowledgeGraph,
    MetaNode,
)
from translator_tom.v1_6.models.meta_qualifier import MetaQualifier
from translator_tom.v1_6.models.node_binding import NodeBinding
from translator_tom.v1_6.models.path_binding import PathBinding
from translator_tom.v1_6.models.path_constraint import PathConstraint
from translator_tom.v1_6.models.qualifier import Qualifier, QualifierConstraint
from translator_tom.v1_6.models.query import Query
from translator_tom.v1_6.models.query_graph import (
    BaseQueryGraph,
    PathfinderQueryGraph,
    QEdge,
    QNode,
    QPath,
    QueryGraph,
    SetInterpretation,
    SetInterpretationEnum,
)
from translator_tom.v1_6.models.response import Response
from translator_tom.v1_6.models.result import Result
from translator_tom.v1_6.models.retrieval_source import (
    ResourceRole,
    ResourceRoleEnum,
    RetrievalSource,
)
from translator_tom.v1_6.models.workflow_operations import (
    Operation,
)

# `diff` imports `TOMBase` from the top-level package, so it must load after
# `TOMBase` is bound above (isort would otherwise reorder it and cause a
# partially-initialized-module circular import).
from translator_tom.v1_6.diff import Delta, diff  # isort: skip
