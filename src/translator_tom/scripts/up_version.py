"""Up-version a TRAPI 1.6 JSON file to TRAPI 2.0.

Installed as the ``tom-up-version`` command (also runnable via
``python -m translator_tom.scripts.up_version``)::

    tom-up-version Response response_1_6.json -o response_2_0.json
    tom-up-version Query query_1_6.json                # 2.0 JSON to stdout

``model`` is the TRAPI 1.6 object the input represents (e.g. Response, Query, Message).
The converted 2.0 JSON is written to ``--out`` if given, otherwise to stdout.

Runs on the raw dict via the ``model_dicts`` converter (no model construction), which is
several times faster than the model layer for large responses. The input is validated
against the 1.6 schema on load (a cached ``TypeAdapter`` pass, still no model built).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import orjson

from translator_tom.model_dicts import dict_up_version
from translator_tom.scripts._common import (
    exported_dict_utils,
    load_dict_or_report,
    write_bytes_or_report,
)
from translator_tom.v1_6 import model_dicts as v1_6_model_dicts

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
    """Load the 1.6 file named on the command line and emit its 2.0 conversion."""
    args = _build_parser().parse_args(argv)

    data, model, code = load_dict_or_report(
        args.model, Path(args.file), exported_dict_utils(v1_6_model_dicts)
    )
    if data is None or model is None:
        return code

    # broad catch at the CLI boundary: report cleanly rather than dumping a traceback
    try:
        converted = dict_up_version(data, model)
    except Exception as exc:
        print(f"✗ {args.file} could not be up-versioned to 2.0: {exc}", file=sys.stderr)
        return 1

    output = orjson.dumps(converted)
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
