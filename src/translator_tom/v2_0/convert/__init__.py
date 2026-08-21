"""TRAPI 1.6 → 2.0 conversion (shared transforms for the model and dict layers).

`up_version(obj)` upgrades any TRAPI 1.6 TOM model (a whole `Response`/`Query` tree or
an individual sub-model) to its 2.0 equivalent, dispatched on the source type.
`dict_up_version(data, source)` applies the same transforms to a raw 1.6 dict, producing
a 2.0-shaped dict without constructing models.
"""

# Import all registration modules to trigger @register side effects.
from translator_tom.v2_0.convert import _analysis as _analysis
from translator_tom.v2_0.convert import _auxiliary_graph as _auxiliary_graph
from translator_tom.v2_0.convert import _bindings as _bindings
from translator_tom.v2_0.convert import _knowledge_graph as _knowledge_graph
from translator_tom.v2_0.convert import _message as _message
from translator_tom.v2_0.convert import _path_constraint as _path_constraint
from translator_tom.v2_0.convert import _qualifier as _qualifier
from translator_tom.v2_0.convert import _query as _query
from translator_tom.v2_0.convert import _query_graph as _query_graph
from translator_tom.v2_0.convert import _response as _response
from translator_tom.v2_0.convert import _result as _result
from translator_tom.v2_0.convert._util import dict_up_version, up_version

__all__ = ["dict_up_version", "up_version"]
