"""TRAPI 1.6 → 2.0 model conversion.

`convert(obj)` upgrades any TRAPI 1.6 TOM model (a whole `Response`/`Query` tree or
an individual sub-model) to its TRAPI 2.0 equivalent, dispatched on the source type.
"""

# Import all registration modules to trigger @convert.register side effects.
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
from translator_tom.v2_0.convert._util import up_version

__all__ = ["up_version"]
