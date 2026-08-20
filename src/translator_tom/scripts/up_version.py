"""Up-version a TRAPI 1.6 JSON file to TRAPI 2.0.

Installed as the ``tom-up-version`` command (also runnable via
``python -m translator_tom.scripts.up_version``)::

    tom-up-version Response response_1_6.json -o response_2_0.json
    tom-up-version Query query_1_6.json                # 2.0 JSON to stdout

``model`` is the TRAPI 1.6 object the input represents (e.g. Response, Query, Message).
The converted 2.0 JSON is written to ``--out`` if given, otherwise to stdout.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ValidationError

from translator_tom import v1_6
from translator_tom.scripts._common import (
    exported_models,
    load_parse_or_report,
    write_bytes_or_report,
)
from translator_tom.v2_0 import up_version

if TYPE_CHECKING:
    from collections.abc import Sequence


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tom-up-version",
        description="Up-version a TRAPI 1.6 JSON file to TRAPI 2.0.",
    )
    parser.add_argument(
        "model", help="TRAPI 1.6 model the input represents, e.g. Response"
    )
    parser.add_argument("file", help="path to a TRAPI 1.6 JSON file")
    parser.add_argument(
        "-o",
        "--out",
        metavar="PATH",
        help="write the converted 2.0 JSON to PATH (default: stdout)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Parse the 1.6 file named on the command line and emit its 2.0 conversion."""
    args = _build_parser().parse_args(argv)

    instance, code = load_parse_or_report(
        args.model, Path(args.file), models=exported_models(v1_6)
    )
    if instance is None:
        return code

    try:
        converted = up_version(instance)
    except ValidationError as exc:
        print(
            f"✗ {args.file} could not be up-versioned to 2.0:\n{exc}", file=sys.stderr
        )
        return 1

    output = converted.to_json()
    if args.out is None:
        sys.stdout.buffer.write(output + b"\n")
        return 0

    out = Path(args.out)
    if code := write_bytes_or_report(out, output):
        return code
    print(f"✓ Up-versioned {args.file} ({args.model}) → {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
