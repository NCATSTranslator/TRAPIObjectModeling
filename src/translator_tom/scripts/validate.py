"""Parse a file into a named model, then run semantic validation on the result.

Installed as the ``tom-validate`` command (also runnable via
``python -m translator_tom.scripts.validate``)::

    tom-validate Response response.json
    tom-validate Response response_1_6.json --version 1.6

The file is parsed and semantically validated as ``model`` at the given
``--version`` (default ``2.0``). Exits ``0`` when validation finds no errors and
``1`` when it does, so it can be used as a check in scripts or CI. Warnings are
reported but do not fail the run.
"""

from __future__ import annotations

import argparse
import importlib
from pathlib import Path
from typing import TYPE_CHECKING

from translator_tom.scripts._common import (
    DEFAULT_VERSION,
    VERSIONS,
    exported_models,
    import_version,
    load_parse_or_report,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from translator_tom.validation import (
        SemanticValidationError,
        SemanticValidationWarning,
    )


def _format_entry(entry: SemanticValidationError | SemanticValidationWarning) -> str:
    """Render a validation error/warning as an indented, location-prefixed line."""
    location = ".".join(str(part) for part in entry.location) or "<root>"
    return f"  [{location}] {entry.message}"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tom-validate",
        description=(
            "Parse a JSON file into a TRAPI object model, then run semantic "
            "validation on it. Exits non-zero if validation finds errors."
        ),
    )
    parser.add_argument("model", help="model class name to parse into, e.g. Response")
    parser.add_argument("file", help="path to a JSON file")
    parser.add_argument(
        "-V",
        "--version",
        choices=VERSIONS,
        default=DEFAULT_VERSION,
        help=f"TRAPI version of the input (default: {DEFAULT_VERSION})",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Parse and semantically validate the file named on the command line."""
    args = _build_parser().parse_args(argv)

    namespace = import_version(args.version)
    models = exported_models(namespace)

    instance, code = load_parse_or_report(args.model, Path(args.file), models=models)
    if instance is None:
        return code
    print(f"✓ Parsed {args.file} as {args.model}")

    validation = importlib.import_module(f"{namespace.__name__}.validation")
    warnings, errors = validation.semantic_validate(instance)

    print(f"\nWarnings ({len(warnings)}):")
    for warning in warnings:
        print(_format_entry(warning))
    print(f"\nErrors ({len(errors)}):")
    for error in errors:
        print(_format_entry(error))

    print(f"\nSemantic validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
