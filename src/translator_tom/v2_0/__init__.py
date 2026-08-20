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
    "AgentTypeConstraint",
    "AllowDenyConstraint",
    "AllowDenyConstraintBehavior",
    "AllowDenyConstraintBehaviorEnum",
    "Analysis",
    "AsyncQuery",
    "AsyncQueryResponse",
    "AsyncQueryStatusResponse",
    "Attribute",
    "AttributeConstraint",
    "AuxGraphID",
    "AuxiliaryGraph",
    "AuxiliaryGraphsDict",
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
    "KnowledgeLevelConstraint",
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
    "QEdge",
    "QEdgeConstraints",
    "QEdgeID",
    "QNode",
    "QNodeID",
    "QPath",
    "QPathID",
    "Qualifier",
    "QualifierSetConstraint",
    "Query",
    "QueryGraph",
    "QueryParameters",
    "ResourceRole",
    "ResourceRoleEnum",
    "Response",
    "Result",
    "RetrievalSource",
    "SetInterpretation",
    "SetInterpretationEnum",
    "SourceConstraint",
    "TOMBase",
    "diff",
    "infores",
    "register_union_discriminator",
    "tomhash",
    "tomhash_int",
    "tomhash_to_int",
    "up_version",
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
from translator_tom.v2_0.models import workflow_operations as workflow
from translator_tom.v2_0.models.analysis import Analysis
from translator_tom.v2_0.models.asyncquery import (
    AsyncQuery,
    AsyncQueryResponse,
    AsyncQueryStatusResponse,
)
from translator_tom.v2_0.models.attribute import (
    Attribute,
    AttributeConstraint,
    Operator,
    OperatorEnum,
)
from translator_tom.v2_0.models.auxiliary_graph import (
    AuxiliaryGraph,
    AuxiliaryGraphsDict,
)
from translator_tom.v2_0.models.constraints import (
    AgentTypeConstraint,
    AllowDenyConstraint,
    AllowDenyConstraintBehavior,
    AllowDenyConstraintBehaviorEnum,
    KnowledgeLevelConstraint,
    QEdgeConstraints,
    SourceConstraint,
)
from translator_tom.v2_0.models.edge_binding import EdgeBinding
from translator_tom.v2_0.models.knowledge_graph import Edge, KnowledgeGraph, Node
from translator_tom.v2_0.models.log_entry import LogEntry, LogLevel, LogLevelEnum
from translator_tom.v2_0.models.message import Message
from translator_tom.v2_0.models.meta_attribute import MetaAttribute
from translator_tom.v2_0.models.meta_knowledge_graph import (
    MetaEdge,
    MetaKnowledgeGraph,
    MetaNode,
)
from translator_tom.v2_0.models.meta_qualifier import MetaQualifier
from translator_tom.v2_0.models.node_binding import NodeBinding
from translator_tom.v2_0.models.path_binding import PathBinding
from translator_tom.v2_0.models.path_constraint import PathConstraint
from translator_tom.v2_0.models.qualifier import Qualifier, QualifierSetConstraint
from translator_tom.v2_0.models.query import Query
from translator_tom.v2_0.models.query_graph import (
    QEdge,
    QNode,
    QPath,
    QueryGraph,
    SetInterpretation,
    SetInterpretationEnum,
)
from translator_tom.v2_0.models.query_parameters import QueryParameters
from translator_tom.v2_0.models.response import Response
from translator_tom.v2_0.models.result import Result
from translator_tom.v2_0.models.retrieval_source import (
    ResourceRole,
    ResourceRoleEnum,
    RetrievalSource,
)
from translator_tom.v2_0.models.workflow_operations import (
    Operation,
)

# `diff` and `convert` reach back into this package's namespace, so they must load
# after the symbols above are bound (isort would otherwise reorder them and cause a
# partially-initialized-module circular import).
from translator_tom.v2_0.diff import Delta, diff  # isort: skip
from translator_tom.v2_0.convert import up_version  # isort: skip
