"""Shared helpers for the ``translator_tom`` command-line scripts."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import orjson
from pydantic import ValidationError

import translator_tom
from translator_tom.utils.object_base import TOMBase

if TYPE_CHECKING:
    from types import ModuleType

VERSIONS = ("1.6", "2.0")  # user-facing TRAPI versions
DEFAULT_VERSION = "2.0"


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


def load_parse_or_report(
    model_name: str,
    path: Path,
    models: dict[str, type[TOMBase]] | None = None,
) -> tuple[TOMBase | None, int]:
    """Parse ``path`` into the named model, printing a diagnostic on failure.

    Returns ``(instance, exit_code)`` where ``instance`` is ``None`` on failure
    and ``exit_code`` is a process return code (``0`` on success). Shared by the
    ``parse``, ``validate``, and ``up-version`` entry points so they report problems
    identically. ``models`` overrides the model registry to resolve ``model_name``
    against (defaults to the latest-version exports); ``up-version`` passes the 1.6 set.
    """
    if models is None:
        models = exported_models()
    model = models.get(model_name)
    if model is None:
        print(
            f"error: unknown model {model_name!r}. Available models:", file=sys.stderr
        )
        print("  " + ", ".join(sorted(models)), file=sys.stderr)
        return None, 2
    if not path.is_file():
        print(f"error: file missing: {path}", file=sys.stderr)
        return None, 2
    try:
        instance = model.from_json(path.read_bytes())
    except OSError as exc:
        print(f"error: could not read {path}: {exc}", file=sys.stderr)
        return None, 2
    except orjson.JSONDecodeError as exc:
        print(f"✗ {path} is not valid JSON: {exc}", file=sys.stderr)
        return None, 1
    except ValidationError as exc:
        print(
            f"✗ {path} failed to parse to model: {model_name}:\n{exc}", file=sys.stderr
        )
        return None, 1
    return instance, 0


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
