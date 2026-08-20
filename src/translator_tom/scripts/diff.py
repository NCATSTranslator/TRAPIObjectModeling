"""Diff two TRAPI JSON files parsed as the same model, emitting the deltas as JSON.

Installed as the ``tom-diff`` command (also runnable via
``python -m translator_tom.scripts.diff``)::

    tom-diff Response a.json b.json                         # deltas to stdout
    tom-diff Message a.json b.json --normalize -o diff.json
    tom-diff Response a.json b.json --version 1.6

Both files are parsed as ``model`` at the given ``--version`` (default ``2.0``); the
`diff` deltas are written as a JSON array to ``--output`` if given, otherwise to stdout.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import orjson

from translator_tom.scripts._common import (
    DEFAULT_VERSION,
    VERSIONS,
    exported_models,
    import_version,
    load_parse_or_report,
    write_bytes_or_report,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tom-diff",
        description="Diff two TRAPI JSON files (parsed as the same model) as JSON deltas.",
    )
    parser.add_argument(
        "model", help="model class name to parse both files into, e.g. Response"
    )
    parser.add_argument("left", help="path to the baseline JSON file")
    parser.add_argument("right", help="path to the new JSON file")
    parser.add_argument(
        "-V",
        "--version",
        choices=VERSIONS,
        default=DEFAULT_VERSION,
        help=f"TRAPI version of the inputs (default: {DEFAULT_VERSION})",
    )
    parser.add_argument(
        "-s",
        "--strict",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="report every field difference (default); --no-strict skips equal-hash subtrees",
    )
    parser.add_argument(
        "-n",
        "--normalize",
        action="store_true",
        help="compare normalized copies (re-key edges by hash); Message/Response only",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="PATH",
        help="write the diff JSON to PATH (default: stdout)",
    )
    return parser


def _delta_to_dict(delta: Any) -> dict[str, Any]:
    """Render a diff `Delta` as a JSON-ready dict."""
    return {
        "path": list(delta.path),
        "kind": delta.kind,
        "left": delta.left,
        "right": delta.right,
        "locator": delta.locator,
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Parse both files as the named model + version and emit their diff as JSON."""
    args = _build_parser().parse_args(argv)

    namespace = import_version(args.version)
    models = exported_models(namespace)

    left, code = load_parse_or_report(args.model, Path(args.left), models=models)
    if left is None:
        return code
    right, code = load_parse_or_report(args.model, Path(args.right), models=models)
    if right is None:
        return code

    try:
        deltas = namespace.diff(
            left, right, strict=args.strict, normalize=args.normalize
        )
    except ValueError as exc:
        print(f"✗ cannot diff: {exc}", file=sys.stderr)
        return 1

    output = orjson.dumps(
        [_delta_to_dict(delta) for delta in deltas],
        option=orjson.OPT_INDENT_2,
        default=str,
    )

    if args.output is None:
        sys.stdout.buffer.write(output + b"\n")
        return 0

    out = Path(args.output)
    if code := write_bytes_or_report(out, output):
        return code
    print(f"✓ Wrote {len(deltas)} diff(s) to {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
