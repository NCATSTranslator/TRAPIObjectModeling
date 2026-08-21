"""Shared helpers for the ``translator_tom`` command-line scripts."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

import orjson
from pydantic import ValidationError

import translator_tom
from translator_tom.utils.dict_util_base import DictUtil
from translator_tom.utils.object_base import TOMBase

if TYPE_CHECKING:
    from types import ModuleType

VERSIONS = ("1.6", "2.0")  # user-facing TRAPI versions
DEFAULT_VERSION = "2.0"

_Resolved = TypeVar("_Resolved")


def import_version(version: str) -> ModuleType:
    """Import the `translator_tom` subpackage for a TRAPI version (e.g. `2.0` -> `v2_0`)."""
    return importlib.import_module(f"translator_tom.v{version.replace('.', '_')}")


def exported_models(namespace: ModuleType = translator_tom) -> dict[str, type[TOMBase]]:
    """Map a version namespace's exported model names to their ``TOMBase`` subclass.

    Defaults to the latest-version (``translator_tom``) exports; pass
    ``translator_tom.v1_6`` for the 1.6 source models.
    """
    models: dict[str, type[TOMBase]] = {}
    for name in getattr(namespace, "__all__", ()):
        obj = getattr(namespace, name)
        if isinstance(obj, type) and issubclass(obj, TOMBase) and obj is not TOMBase:
            models[name] = obj
    return models


def exported_dict_utils(
    namespace: ModuleType,
) -> dict[str, type[DictUtil[Any]]]:
    """Map a ``model_dicts`` namespace's ``*DictUtil`` classes by their model name.

    Pass e.g. ``translator_tom.v1_6.model_dicts`` to get ``{"Response": ResponseDictUtil,
    …}`` — keyed by the mirrored model's name so callers resolve the same names as
    ``exported_models``.
    """
    utils: dict[str, type[DictUtil[Any]]] = {}
    for name in getattr(namespace, "__all__", ()):
        obj = getattr(namespace, name)
        if isinstance(obj, type) and issubclass(obj, DictUtil):
            utils[obj._model.__name__] = obj
    return utils


def _resolve_and_read(
    name: str, path: Path, registry: dict[str, _Resolved]
) -> tuple[bytes | None, _Resolved | None, int]:
    """Resolve ``name`` in ``registry`` and read ``path``'s bytes, reporting failures.

    Returns ``(raw_bytes, resolved, exit_code)``; the first two are ``None`` on failure.
    Shared by the model- and dict-based loaders below.
    """
    resolved = registry.get(name)
    if resolved is None:
        print(f"error: unknown model {name!r}. Available models:", file=sys.stderr)
        print("  " + ", ".join(sorted(registry)), file=sys.stderr)
        return None, None, 2
    if not path.is_file():
        print(f"error: file missing: {path}", file=sys.stderr)
        return None, None, 2
    try:
        raw = path.read_bytes()
    except OSError as exc:
        print(f"error: could not read {path}: {exc}", file=sys.stderr)
        return None, None, 2
    return raw, resolved, 0


def load_parse_or_report(
    model_name: str,
    path: Path,
    models: dict[str, type[TOMBase]] | None = None,
) -> tuple[TOMBase | None, int]:
    """Parse ``path`` into the named model, printing a diagnostic on failure.

    Returns ``(instance, exit_code)`` where ``instance`` is ``None`` on failure
    and ``exit_code`` is a process return code (``0`` on success). Shared by the
    ``parse`` and ``validate`` entry points so they report problems identically.
    """
    if models is None:
        models = exported_models()
    raw, model, code = _resolve_and_read(model_name, path, models)
    if raw is None or model is None:
        return None, code
    try:
        instance = model.from_json(raw)
    except orjson.JSONDecodeError as exc:
        print(f"✗ {path} is not valid JSON: {exc}", file=sys.stderr)
        return None, 1
    except ValidationError as exc:
        print(
            f"✗ {path} failed to parse to model: {model_name}:\n{exc}", file=sys.stderr
        )
        return None, 1
    return instance, 0


def load_dict_or_report(
    model_name: str,
    path: Path,
    dict_utils: dict[str, type[DictUtil[Any]]],
) -> tuple[dict[str, Any] | None, type[TOMBase] | None, int]:
    """Load ``path`` as a validated raw dict via its ``*DictUtil`` (no model construction).

    Returns ``(data, model, exit_code)``; ``data``/``model`` are ``None`` on failure. The
    dict is validated against the schema (``from_json(validate=True)``, a cached
    ``TypeAdapter`` pass with no model construction) so malformed input is reported the
    same way as the model loaders. ``model`` is the mirrored model class, ready to pass as
    the ``dict_up_version`` source. Drives the fast dict-layer ``up-version`` converter.
    """
    raw, util, code = _resolve_and_read(model_name, path, dict_utils)
    if raw is None or util is None:
        return None, None, code
    try:
        data = util.from_json(raw, validate=True)
    except orjson.JSONDecodeError as exc:
        print(f"✗ {path} is not valid JSON: {exc}", file=sys.stderr)
        return None, None, 1
    except ValidationError as exc:
        print(
            f"✗ {path} failed to validate as 1.6 {model_name}:\n{exc}", file=sys.stderr
        )
        return None, None, 1
    return data, util._model, 0


def write_bytes_or_report(path: Path, data: bytes) -> int:
    """Write ``data`` to ``path``, reporting an OS error to stderr.

    Returns a process exit code: ``0`` on success, ``2`` if the write failed.
    """
    try:
        path.write_bytes(data)
    except OSError as exc:
        print(f"error: could not write {path}: {exc}", file=sys.stderr)
        return 2
    return 0
