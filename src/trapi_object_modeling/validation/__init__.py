"""Semantic validation for TOM objects via singledispatch."""

# Import all registration modules to trigger @singledispatch.register side effects
from trapi_object_modeling.validation import _analysis as _analysis
from trapi_object_modeling.validation import _asyncquery as _asyncquery
from trapi_object_modeling.validation import _attribute as _attribute
from trapi_object_modeling.validation import (
    _attribute_constraint as _attribute_constraint,
)
from trapi_object_modeling.validation import _edge_binding as _edge_binding
from trapi_object_modeling.validation import _knowledge_graph as _knowledge_graph
from trapi_object_modeling.validation import _log_entry as _log_entry
from trapi_object_modeling.validation import _message as _message
from trapi_object_modeling.validation import _meta_attribute as _meta_attribute
from trapi_object_modeling.validation import (
    _meta_knowledge_graph as _meta_knowledge_graph,
)
from trapi_object_modeling.validation import _meta_qualifier as _meta_qualifier
from trapi_object_modeling.validation import _node_binding as _node_binding
from trapi_object_modeling.validation import _path_binding as _path_binding
from trapi_object_modeling.validation import _path_constraint as _path_constraint
from trapi_object_modeling.validation import _qualifier as _qualifier
from trapi_object_modeling.validation import (
    _qualifier_constraint as _qualifier_constraint,
)
from trapi_object_modeling.validation import _query_graph as _query_graph
from trapi_object_modeling.validation import _response as _response
from trapi_object_modeling.validation import _result as _result
from trapi_object_modeling.validation import (
    _retrieval_source as _retrieval_source,
)
from trapi_object_modeling.validation import (
    _workflow_operations as _workflow_operations,
)
from trapi_object_modeling.validation._util import (
    Location,
    SemanticValidationError,
    SemanticValidationErrorList,
    SemanticValidationResult,
    SemanticValidationWarning,
    SemanticValidationWarningList,
    passes_semantic_validation,
    semantic_validate,
    valid_if_missing,
    validate_many,
)

__all__ = [
    "Location",
    "SemanticValidationError",
    "SemanticValidationErrorList",
    "SemanticValidationResult",
    "SemanticValidationWarning",
    "SemanticValidationWarningList",
    "passes_semantic_validation",
    "semantic_validate",
    "valid_if_missing",
    "validate_many",
]
