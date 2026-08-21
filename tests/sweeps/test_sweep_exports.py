"""Reflection-driven export / ``__all__`` integrity sweep, over every version package.

Enforces the codebase convention that every public symbol lives in its module's
``__all__`` *and* is re-exported from its **version package** root: models and shared
utils flatten into ``translator_tom.v<ver>``; the dict layer flattens into
``translator_tom.v<ver>.model_dicts``. (The top-level ``translator_tom`` then re-exports
the latest version wholesale.) The checks are purely reflective, so new
models/DictUtils/versions are covered automatically and any hand-maintained drift (stale
``__all__`` entry, forgotten re-export) is caught.

Intentional exceptions live in the documented allow-sets below.
"""

from __future__ import annotations

import importlib
import pkgutil
from types import ModuleType
from typing import Any

import pytest
from _sweep_helpers import VERSIONS, dictutils_of, models_of, sweep_id

import translator_tom.utils
from translator_tom import TOMBase
from translator_tom.utils.dict_util_base import DictUtil

# --- allow-sets ------------------------------------------------------------------------

# Submodules re-exported wholesale as a *namespace* attribute rather than flattened into
# the version __all__. Their members live under ``<version>.<attr>`` (models) /
# ``<version>.model_dicts.<attr>`` (dicts). Maps submodule short-name -> namespace attr.
NAMESPACE_MODULES = {"workflow_operations": "workflow"}

# Symbols intentionally in a submodule __all__ but not flattened into the package __all__.
EXPECTED_NOT_REEXPORTED = {
    ("cache", "lru_copy_cache"): (
        "internal caching helper; consumed via translator_tom.utils.cache within the "
        "library, not part of the flat public API"
    ),
}

# Known REAL drift: name in a submodule __all__ but never re-exported -> xfail(strict=False).
KNOWN_MISSING_REEXPORT: dict[tuple[str, str], str] = {}

# Models/base classes to pin re-export identity against (invariant 4). Model module paths
# are templated per version (``{v}`` -> version package name); shared-infra paths are
# absolute (they live in the shared ``translator_tom.utils``).
IDENTITY_CHECKS = {
    "Query": "{v}.models.query",
    "KnowledgeGraph": "{v}.models.knowledge_graph",
    "Message": "{v}.models.message",
    "Analysis": "{v}.models.analysis",
    "RetrievalSource": "{v}.models.retrieval_source",
    "TOMBase": "translator_tom.utils.object_base",
    "DictUtil": "translator_tom.utils.dict_util_base",
}


def _vlabel(version: ModuleType) -> str:
    return version.__name__.rsplit(".", 1)[-1]


def _model_dicts(version: ModuleType) -> ModuleType:
    return importlib.import_module(f"{version.__name__}.model_dicts")


def _submodule_all_params() -> list[Any]:
    """(flat_pkg, submodule, name) for every submodule ``__all__`` entry, across versions.

    ``flat_pkg`` is the package whose ``__all__`` the name is expected to flatten into
    (the version root for models/utils, the version ``model_dicts`` for the dict layer).
    """
    params: list[Any] = []
    for version in VERSIONS:
        models_pkg = importlib.import_module(f"{version.__name__}.models")
        dicts_pkg = _model_dicts(version)
        for flat_pkg, package in (
            (version, models_pkg),
            (version, translator_tom.utils),
            (dicts_pkg, dicts_pkg),
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

_TOPLEVEL_ALL = [
    pytest.param(v, name, id=f"{_vlabel(v)}:{name}") for v in VERSIONS for name in v.__all__
]
_MODEL_DICTS_ALL = [
    pytest.param(v, name, id=f"{_vlabel(v)}:{name}")
    for v in VERSIONS
    for name in _model_dicts(v).__all__
]
_MODELS = [pytest.param(v, m, id=sweep_id(m)) for v in VERSIONS for m in models_of(v)]
_DICTUTILS = [
    pytest.param(v, m, du, id=sweep_id(du))
    for v in VERSIONS
    for m, du in dictutils_of(v)
]
_IDENTITY = [
    pytest.param(v, name, path, id=f"{_vlabel(v)}:{name}")
    for v in VERSIONS
    for name, path in IDENTITY_CHECKS.items()
]


# --- (1) version __all__ entries all resolve -------------------------------------------


@pytest.mark.parametrize(("version", "name"), _TOPLEVEL_ALL)
def test_version_all_resolves(version: ModuleType, name: str) -> None:
    assert hasattr(version, name), (
        f"{version.__name__}.__all__ lists {name!r} but it is not an attribute"
    )


@pytest.mark.parametrize(("version", "name"), _MODEL_DICTS_ALL)
def test_model_dicts_all_resolves(version: ModuleType, name: str) -> None:
    dicts = _model_dicts(version)
    assert hasattr(dicts, name), (
        f"{dicts.__name__}.__all__ lists {name!r} but it is not an attribute"
    )


# --- (2) no public model / DictUtil omitted from its namespace -------------------------


@pytest.mark.parametrize(("version", "model"), _MODELS)
def test_model_reexported_from_version(
    version: ModuleType, model: type[TOMBase]
) -> None:
    assert model.__name__ in version.__all__, (
        f"{model.__name__} is a public model but missing from {version.__name__}.__all__"
    )
    assert getattr(version, model.__name__) is model


@pytest.mark.parametrize("version", VERSIONS, ids=_vlabel)
def test_dictutil_base_reexported(version: ModuleType) -> None:
    assert "DictUtil" in version.__all__
    assert version.DictUtil is DictUtil


@pytest.mark.parametrize(("version", "model", "dictutil"), _DICTUTILS)
def test_dictutil_reexported(
    version: ModuleType, model: type[TOMBase], dictutil: type[DictUtil[Any]]
) -> None:
    dicts = _model_dicts(version)
    short = dictutil.__module__.rsplit(".", 1)[-1]
    if short in NAMESPACE_MODULES:  # namespaced (workflow ops), not in the flat __all__
        namespace = getattr(dicts, NAMESPACE_MODULES[short])
        assert getattr(namespace, dictutil.__name__) is dictutil
        return
    assert dictutil.__name__ in dicts.__all__, (
        f"{dictutil.__name__} is a product DictUtil but missing from {dicts.__name__}.__all__"
    )
    assert getattr(dicts, dictutil.__name__) is dictutil


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


@pytest.mark.parametrize(("version", "name", "module_path"), _IDENTITY)
def test_reexport_identity(version: ModuleType, name: str, module_path: str) -> None:
    module = importlib.import_module(module_path.format(v=version.__name__))
    assert getattr(version, name) is getattr(module, name)
