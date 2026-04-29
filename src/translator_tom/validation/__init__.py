"""Semantic validation methods for all models."""

# Import all registration modules to trigger @singledispatch.register side effects.
from translator_tom.validation import _analysis as _analysis
from translator_tom.validation import _asyncquery as _asyncquery
from translator_tom.validation import (
    _attribute as _attribute,
)
from translator_tom.validation import _auxiliary_graph as _auxiliary_graph
from translator_tom.validation import _edge_binding as _edge_binding
from translator_tom.validation import _knowledge_graph as _knowledge_graph
from translator_tom.validation import _log_entry as _log_entry
from translator_tom.validation import _message as _message
from translator_tom.validation import _meta_attribute as _meta_attribute
from translator_tom.validation import (
    _meta_knowledge_graph as _meta_knowledge_graph,
)
from translator_tom.validation import _meta_qualifier as _meta_qualifier
from translator_tom.validation import _node_binding as _node_binding
from translator_tom.validation import _path_binding as _path_binding
from translator_tom.validation import _path_constraint as _path_constraint
from translator_tom.validation import (
    _qualifier as _qualifier,
)
from translator_tom.validation import _query as _query
from translator_tom.validation import _query_graph as _query_graph
from translator_tom.validation import _response as _response
from translator_tom.validation import _result as _result
from translator_tom.validation import (
    _retrieval_source as _retrieval_source,
)
from translator_tom.validation import (
    _workflow_operations as _workflow_operations,
)
from translator_tom.validation._util import (
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
