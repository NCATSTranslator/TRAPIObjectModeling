"""Shared corpus helpers for the standalone benchmark scripts in this folder.

Kept stdlib-only on purpose: the scripts time the `translator_tom` import, so
importing this module must not pull in `translator_tom` (or any heavy dep) and
perturb that measurement. `import_version` imports it lazily, only when a script
calls it inside its timed section.

Every bench takes a ``--version`` arg (``1.6``/``2.0``) selecting both the corpus
directory and the model set, so a bench can run against any supported TRAPI version.
"""

import argparse
import gzip
import importlib
from pathlib import Path
from types import ModuleType

VERSIONS = ("1.6", "2.0")  # user-facing TRAPI versions
DEFAULT_VERSION = "2.0"
CORPUS_BASE = Path("data/example_trapi")


def _package(version: str) -> str:
    """Map a user-facing TRAPI version to its package/dir name (e.g. `2.0` -> `v2_0`)."""
    return f"v{version.replace('.', '_')}"


def parse_version(description: str | None = None) -> str:
    """Parse the shared ``--version`` CLI arg, returning the selected TRAPI version."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-v",
        "--version",
        choices=VERSIONS,
        default=DEFAULT_VERSION,
        help=f"TRAPI version to bench: corpus dir + models (default: {DEFAULT_VERSION})",
    )
    return parser.parse_args().version


def corpus_root(version: str) -> Path:
    """The example-corpus directory for `version`."""
    return CORPUS_BASE / _package(version)


def import_version(version: str, submodule: str = "") -> ModuleType:
    """Import and return a `translator_tom` version subpackage, or a submodule of it.

    Imported lazily (only when a script calls this, inside its timed section) so that
    importing `utils` never pulls in `translator_tom`.
    """
    name = f"translator_tom.{_package(version)}"
    if submodule:
        name = f"{name}.{submodule}"
    return importlib.import_module(name)


def discover_files(root: Path) -> list[Path]:
    """Return every `.json` and `.json.gz` under `root`, sorted by bucket size.

    Buckets are the immediate-parent directory name (`<N>mb`); we sort by N
    rather than by on-disk size since gzipped files compress smaller than
    their uncompressed JSON.
    """

    def bucket_size(p: Path) -> int:
        name = p.parent.name.removesuffix("mb")
        return int(name) if name.isdigit() else 0

    paths = [p for p in root.rglob("*") if p.is_file() and p.suffix in (".json", ".gz")]
    return sorted(paths, key=lambda p: (bucket_size(p), p.name))


def read_corpus_file(path: Path) -> str:
    """Read a corpus file as text, transparently decompressing `.gz`."""
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return f.read()
    with path.open() as f:
        return f.read()
