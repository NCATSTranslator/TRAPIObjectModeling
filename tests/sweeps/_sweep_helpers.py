"""Shared harness for the reflection-driven `test_sweep_*` suites.

The sweeps run over **every** installed TRAPI version package
(`translator_tom.v<major>_<minor>`), discovered dynamically. `MODELS`/`DICTUTILS` are
the union across versions (each carries its version in `__module__`), and `build()`
makes a bare, minimal instance of any model from its field annotations. `VERSIONS`
exposes the version packages themselves for the structure-aware export sweep. Use
`sweep_id()` for parametrize ids so same-named models from different versions stay
distinct (e.g. `v1_6:Response` vs `v2_0:Response`).
"""

from __future__ import annotations

import enum
import importlib
import pkgutil
import re
import types
from types import ModuleType
from typing import Any, Literal, Union, get_args, get_origin

import translator_tom
from translator_tom import TOMBase
from translator_tom.utils.dict_util_base import DictUtil

_VERSION_RE = re.compile(r"^v\d+_\d+$")


def discover_versions() -> list[ModuleType]:
    """Import and return every `translator_tom.v<major>_<minor>` version subpackage."""
    versions: list[ModuleType] = []
    for info in pkgutil.iter_modules(translator_tom.__path__):
        if _VERSION_RE.match(info.name):
            module = importlib.import_module(f"translator_tom.{info.name}")
            # ensure the version's DictUtils register into the shared registry
            importlib.import_module(f"translator_tom.{info.name}.model_dicts")
            versions.append(module)
    return sorted(versions, key=lambda m: m.__name__)


VERSIONS = discover_versions()


def version_of(obj: type) -> str:
    """The version segment (e.g. `v2_0`) of a model/DictUtil class's module."""
    return obj.__module__.split(".")[1]


def sweep_id(obj: type) -> str:
    """Version-qualified parametrize id, e.g. `v2_0:Response` / `v2_0:ResponseDictUtil`."""
    return f"{version_of(obj)}:{obj.__name__}"


def models_of(version: ModuleType) -> list[type[TOMBase]]:
    """Public model classes exported from a version package's flat `__all__`."""
    return sorted(
        {
            obj
            for name in version.__all__
            if isinstance((obj := getattr(version, name)), type)
            and issubclass(obj, TOMBase)
            and obj is not TOMBase
        },
        key=lambda c: c.__name__,
    )


def dictutils_of(version: ModuleType) -> list[tuple[type, type]]:
    """`(model, DictUtil)` pairs for a version, from the shared registry.

    Restricted by module prefix so the shared `DictUtil._registry` (which also holds the
    other versions' and test-local throwaway DictUtils) doesn't leak across versions.
    """
    prefix = version.__name__ + "."
    return sorted(
        (
            (model, du)
            for model, du in DictUtil._registry.items()
            if du.__module__.startswith(prefix)
        ),
        key=lambda kv: kv[1].__name__,
    )


# Unions across every version, for the version-agnostic sweeps (each element carries its
# version via __module__; use sweep_id() for distinct parametrize ids).
MODELS = [model for version in VERSIONS for model in models_of(version)]
DICTUTILS = [pair for version in VERSIONS for pair in dictutils_of(version)]


def unwrap(ann: Any) -> Any:
    """Strip `Annotated[X, ...]` down to `X`."""
    while hasattr(ann, "__metadata__"):
        ann = ann.__origin__
    return ann


def dummy(ann: Any) -> Any:
    """Return a minimal, type-correct value for a field annotation (validation skipped)."""
    ann = unwrap(ann)
    origin = get_origin(ann)
    if origin is Union or origin is types.UnionType:
        members = [a for a in get_args(ann) if a is not type(None)]
        return dummy(members[0]) if members else None
    if origin is list:  # one element, to satisfy min_length lists (e.g. Edge.sources)
        elems = get_args(ann)
        return [dummy(elems[0])] if elems else []
    if origin in (set, frozenset, tuple):
        return []
    if origin is dict:  # one entry, to satisfy min_length dicts (e.g. Result nodes)
        args = get_args(ann)
        return {dummy(args[0]): dummy(args[1])} if args else {}
    if origin is Literal:
        return get_args(ann)[0]
    if isinstance(ann, type):
        if issubclass(ann, TOMBase):
            return build(ann)
        if issubclass(ann, enum.Enum):
            return next(iter(ann))
        if issubclass(ann, bool):
            return False
        if issubclass(
            ann, int
        ):  # bool handled above; float below (int is not a float subclass)
            return 0
        if issubclass(ann, float):
            return 0.0
        if issubclass(ann, str):
            return "x"
    return "x"  # Any / unresolved


def build(model: type[TOMBase]) -> TOMBase:
    """A bare, unvalidated instance with only required fields filled by `dummy`."""
    values = {
        name: dummy(field.annotation)
        for name, field in model.model_fields.items()
        if field.is_required()
    }
    return model.model_construct(**values)
