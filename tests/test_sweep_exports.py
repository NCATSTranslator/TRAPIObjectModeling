"""Reflection-driven export / ``__all__`` integrity sweep.

Enforces the codebase convention that every public symbol lives in its module's
``__all__`` *and* is re-exported from the top-level package (models/utils flatten into
``translator_tom``; the dict layer flattens into ``translator_tom.model_dicts``). The
checks are purely reflective, so new models/DictUtils are covered automatically and any
hand-maintained drift (stale ``__all__`` entry, forgotten re-export) is caught.

Intentional exceptions live in the documented allow-sets below. Genuine violations are
reported by failing (or, for the one known-open bug, ``xfail(strict=False)``) rather than
being papered over.
"""

from __future__ import annotations

import importlib
import pkgutil
from types import ModuleType
from typing import Any

import pytest
from _sweep_helpers import DICTUTILS, MODELS

import translator_tom
import translator_tom.model_dicts
import translator_tom.models
import translator_tom.utils
from translator_tom import TOMBase
from translator_tom.utils.dict_util_base import DictUtil

# --- allow-sets ------------------------------------------------------------------------

# Submodules re-exported wholesale as a *namespace* attribute rather than flattened into
# the flat package __all__. Their members live under ``translator_tom.<attr>`` (models) /
# ``translator_tom.model_dicts.<attr>`` (dicts) -- e.g. ``translator_tom.workflow.Operation
# Bind`` -- so the individual operation names are intentionally absent from the flat
# __all__. Maps submodule short-name -> the namespace attribute it is exposed as.
NAMESPACE_MODULES = {"workflow_operations": "workflow"}

# Symbols intentionally in a submodule __all__ but not flattened into the package __all__.
# Keyed (submodule short-name, symbol) -> justification.
EXPECTED_NOT_REEXPORTED = {
    ("cache", "lru_copy_cache"): (
        "internal caching helper; consumed via translator_tom.utils.cache within the "
        "library, not part of the flat public API"
    ),
}

# Known REAL drift: a name listed in a submodule __all__ but never re-exported. Any entry
# here is xfail(strict=False), documenting the bug without editing src. Do NOT hide genuine
# misses in EXPECTED_NOT_REEXPORTED. Currently empty (all known misses fixed).
KNOWN_MISSING_REEXPORT: dict[tuple[str, str], str] = {}

# A handful of models/base classes to pin re-export identity against (invariant 4).
IDENTITY_CHECKS = {
    "Query": "translator_tom.models.query",
    "KnowledgeGraph": "translator_tom.models.knowledge_graph",
    "Message": "translator_tom.models.message",
    "Analysis": "translator_tom.models.analysis",
    "RetrievalSource": "translator_tom.models.retrieval_source",
    "TOMBase": "translator_tom.utils.object_base",
    "DictUtil": "translator_tom.utils.dict_util_base",
}


def _submodule_all_params() -> list[Any]:
    """Yield (flat_package, submodule, name) params for every submodule ``__all__`` entry.

    ``flat_package`` is the package whose ``__all__`` the name is expected to flatten into
    (top-level for models/utils, ``model_dicts`` for the dict layer).
    """
    params: list[Any] = []
    for flat_pkg, package in (
        (translator_tom, translator_tom.models),
        (translator_tom, translator_tom.utils),
        (translator_tom.model_dicts, translator_tom.model_dicts),
    ):
        for info in pkgutil.iter_modules(package.__path__):
            module = importlib.import_module(f"{package.__name__}.{info.name}")
            for name in getattr(module, "__all__", ()):
                marks = (
                    pytest.mark.xfail(
                        reason=KNOWN_MISSING_REEXPORT[info.name, name], strict=False
                    )
                    if (info.name, name) in KNOWN_MISSING_REEXPORT
                    else ()
                )
                ident = module.__name__.removeprefix("translator_tom.")
                params.append(
                    pytest.param(
                        flat_pkg, module, name, marks=marks, id=f"{ident}:{name}"
                    )
                )
    return params


SUBMODULE_ALL_PARAMS = _submodule_all_params()


# --- (1) top-level __all__ entries all resolve -----------------------------------------


@pytest.mark.parametrize("name", translator_tom.__all__)
def test_toplevel_all_resolves(name: str) -> None:
    assert hasattr(translator_tom, name), (
        f"translator_tom.__all__ lists {name!r} but it is not an attribute"
    )


@pytest.mark.parametrize("name", translator_tom.model_dicts.__all__)
def test_model_dicts_all_resolves(name: str) -> None:
    assert hasattr(translator_tom.model_dicts, name), (
        f"translator_tom.model_dicts.__all__ lists {name!r} but it is not an attribute"
    )


# --- (2) no public model / DictUtil omitted from its namespace -------------------------


@pytest.mark.parametrize("model", MODELS, ids=[m.__name__ for m in MODELS])
def test_model_reexported_from_toplevel(model: type[TOMBase]) -> None:
    assert model.__name__ in translator_tom.__all__, (
        f"{model.__name__} is a public model but missing from translator_tom.__all__"
    )
    assert getattr(translator_tom, model.__name__) is model


def test_dictutil_base_reexported() -> None:
    assert "DictUtil" in translator_tom.__all__
    assert translator_tom.DictUtil is DictUtil


@pytest.mark.parametrize(
    ("model", "dictutil"), DICTUTILS, ids=[du.__name__ for _, du in DICTUTILS]
)
def test_dictutil_reexported(
    model: type[TOMBase], dictutil: type[DictUtil[Any]]
) -> None:
    short = dictutil.__module__.rsplit(".", 1)[-1]
    if short in NAMESPACE_MODULES:  # namespaced (workflow ops), not in the flat __all__
        namespace = getattr(translator_tom.model_dicts, NAMESPACE_MODULES[short])
        assert getattr(namespace, dictutil.__name__) is dictutil
        return
    assert dictutil.__name__ in translator_tom.model_dicts.__all__, (
        f"{dictutil.__name__} is a product DictUtil but missing from "
        "translator_tom.model_dicts.__all__"
    )
    assert getattr(translator_tom.model_dicts, dictutil.__name__) is dictutil


# --- (3) + (5) submodule __all__ entries are defined and re-exported -------------------


@pytest.mark.parametrize(("flat_pkg", "module", "name"), SUBMODULE_ALL_PARAMS)
def test_submodule_all_is_reexported(
    flat_pkg: ModuleType, module: ModuleType, name: str
) -> None:
    short = module.__name__.rsplit(".", 1)[-1]
    # (5) the __all__ entry is actually a module attribute (no typos)
    assert hasattr(module, name), (
        f"{module.__name__}.__all__ lists {name!r} but it is not defined"
    )
    # (3) ...and is reachable from the flat package's public API
    if name in flat_pkg.__all__:
        return
    if short in NAMESPACE_MODULES:
        ns_attr = NAMESPACE_MODULES[short]
        assert ns_attr in flat_pkg.__all__, (
            f"namespace {ns_attr!r} for {module.__name__} missing from "
            f"{flat_pkg.__name__}.__all__"
        )
        assert getattr(flat_pkg, ns_attr) is module
        return
    if (short, name) in EXPECTED_NOT_REEXPORTED:
        return
    pytest.fail(
        f"{module.__name__}.{name} is in __all__ but not re-exported from "
        f"{flat_pkg.__name__}.__all__ (public-symbol drift)"
    )


# --- (4) re-export identity (no shadowing / duplicate class) ---------------------------


@pytest.mark.parametrize(
    ("name", "module_path"), IDENTITY_CHECKS.items(), ids=list(IDENTITY_CHECKS)
)
def test_reexport_identity(name: str, module_path: str) -> None:
    module = importlib.import_module(module_path)
    assert getattr(translator_tom, name) is getattr(module, name)
