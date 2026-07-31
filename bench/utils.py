"""Shared corpus helpers for the standalone benchmark scripts in this folder.

Kept stdlib-only on purpose: the scripts time the `translator_tom` import, so
importing this module must not pull in `translator_tom` (or any heavy dep) and
perturb that measurement.
"""

import gzip
from pathlib import Path

CORPUS_ROOT = Path("data/example_trapi")


def discover_files(root: Path = CORPUS_ROOT) -> list[Path]:
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
