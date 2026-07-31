"""Parse a JSON file into a named TRAPI object model.

Installed as ``tom-parse``::

    tom-parse Response response.json
    tom-parse Message message.json --out normalized.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import orjson
from pydantic import ValidationError

import translator_tom
from translator_tom import TOMBase

if TYPE_CHECKING:
    from collections.abc import Sequence


def available_models() -> dict[str, type[TOMBase]]:
    """Return the exported model names mapped to their ``TOMBase`` subclass."""
    models: dict[str, type[TOMBase]] = {}
    for name in translator_tom.__all__:
        obj = getattr(translator_tom, name)
        if isinstance(obj, type) and issubclass(obj, TOMBase) and obj is not TOMBase:
            models[name] = obj
    return models


def parse_file(model: type[TOMBase], path: Path) -> TOMBase:
    """Read ``path`` and parse it into an instance of ``model``."""
    return model.from_json(path.read_bytes())


def load_parse_or_report(model_name: str, path: Path) -> tuple[TOMBase | None, int]:
    """Parse ``path`` into the named model, printing a diagnostic on failure.

    Returns ``(instance, exit_code)`` where ``instance`` is ``None`` on failure
    and ``exit_code`` is a process return code (``0`` on success). Shared by the
    ``parse`` and ``validate`` entry points so both report problems identically.
    """
    models = available_models()
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
        instance = parse_file(model, path)
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


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tom-parse",
        description="Parse a JSON file into a TRAPI Object Model.",
    )
    parser.add_argument("model", help="model class name to parse into, e.g. Response")
    parser.add_argument("file", help="path to a JSON file")
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
    instance, code = load_parse_or_report(args.model, Path(args.file))
    if instance is None:
        return code
    print(f"✓ Parsed {args.file} as {args.model}")
    if args.out is not None:
        out = Path(args.out)
        out.write_bytes(instance.to_json())
        print(f"  wrote normalized JSON to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
