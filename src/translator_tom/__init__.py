"""TRAPI Object Modeling.

The top-level namespace re-exports the latest supported TRAPI version (currently
TRAPI 2.0). To pin a specific version, import it explicitly, e.g.
``from translator_tom.v2_0 import Response`` or ``from translator_tom.v1_6 import Response``.
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _version

try:
    __version__ = _version("translator_tom")
except PackageNotFoundError:  # pragma: no cover - package not installed (source tree)
    __version__ = "0.0.0"

from translator_tom.v2_0 import *  # noqa: F403
from translator_tom.v2_0 import __all__ as __all__
