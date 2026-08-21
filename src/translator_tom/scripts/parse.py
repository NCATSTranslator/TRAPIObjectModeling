"""Parse a JSON file into a named TRAPI object model.

Installed as ``tom-parse``::

    tom-parse Response response.json
    tom-parse Message message.json --out normalized.json
    tom-parse Response response_1_6.json --version 1.6

The file is parsed as ``model`` at the given ``--version`` (default ``2.0``).
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import TYPE_CHECKING

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
        prog="tom-parse",
        description="Parse a JSON file into a TRAPI Object Model.",
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
    parser.add_argument(
        "-o",
        "--out",
        metavar="PATH",
        help="write the parsed model back out as normalized JSON to PATH",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Parse the file named on the command line, reporting success or failure."""
    args = _build_parser().parse_args(argv)

    models = exported_models(import_version(args.version))
    instance, code = load_parse_or_report(args.model, Path(args.file), models=models)
    if instance is None:
        return code
    print(f"✓ Parsed {args.file} as {args.model}")

    if args.out is not None:
        out = Path(args.out)
        if code := write_bytes_or_report(out, instance.to_json()):
            return code
        print(f"  wrote normalized JSON to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
