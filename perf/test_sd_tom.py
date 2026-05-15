"""TOM-only serdes benchmark across every example response.

Walks `data/example_trapi/**` and runs the core (de)serialization paths for
each file. Streams per-file timings in an aligned format as they complete,
then prints a summary table across files at the end.

For a quicker comparison run that also benches reasoner-pydantic on one file
per size bucket, see `perf/test_sd.py`.
"""

import gzip
import time
from pathlib import Path

LABEL_WIDTH = 10
VALUE_FMT = "{:>8.4f}s"
CORPUS_ROOT = Path("data/example_trapi")


def pair_row(
    label: str,
    from_s: float,
    to_s: float,
    bucket: dict[str, tuple[float, float]] | None = None,
) -> None:
    """Print one line with from/to timings; record (from, to) into the bucket."""
    print(
        f"  {label:<{LABEL_WIDTH}}"
        f" from {VALUE_FMT.format(from_s)}"
        f" | to {VALUE_FMT.format(to_s)}"
    )
    if bucket is not None:
        bucket[label] = (from_s, to_s)


def section(title: str) -> None:
    bar = "=" * (len(title) + 2)
    print(f"\n{bar}\n {title}\n{bar}")


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


# --- Import ---

t0 = time.perf_counter()
from translator_tom import Response  # noqa: E402

t_tom = time.perf_counter() - t0

section("Imports")
print(f"  translator_tom Response  {VALUE_FMT.format(t_tom)}")


TEST_FILES = discover_files(CORPUS_ROOT)
print(f"\nDiscovered {len(TEST_FILES)} corpus file(s) under {CORPUS_ROOT}/")

results: dict[str, dict[str, tuple[float, float]]] = {}


for response_path in TEST_FILES:
    label = str(response_path.relative_to(CORPUS_ROOT))
    file_results: dict[str, tuple[float, float]] = {}
    results[label] = file_results

    t0 = time.perf_counter()
    if response_path.suffix == ".gz":
        with gzip.open(response_path, "rt", encoding="utf-8") as f:
            response_json = f.read()
    else:
        with response_path.open() as f:
            response_json = f.read()
    t_read = time.perf_counter() - t0
    size_mb = len(response_json.encode("utf-8")) / 1024 / 1024

    section(f"{label}  ({size_mb:.2f} MB JSON, {t_read:.4f}s)")

    t0 = time.perf_counter()
    response = Response.from_json(response_json)
    t_from_json = time.perf_counter() - t0
    t0 = time.perf_counter()
    _ = response.to_json()
    t_to_json = time.perf_counter() - t0
    pair_row("json", t_from_json, t_to_json, file_results)

    t0 = time.perf_counter()
    response_msgpack = response.to_msgpack()
    t_to_mp = time.perf_counter() - t0
    t0 = time.perf_counter()
    _ = Response.from_msgpack(response_msgpack)
    t_from_mp = time.perf_counter() - t0
    pair_row("msgpack", t_from_mp, t_to_mp, file_results)


# --- Summary ---

section("Summary (seconds): from / to")

short_labels = {
    lbl: lbl.split("/")[-1].removesuffix(".gz").removesuffix(".json")
    for lbl in results
}
ops = list(next(iter(results.values())).keys())


def fmt_cell(v: tuple[float, float] | None) -> str:
    return "—" if v is None else f"{v[0]:.4f} / {v[1]:.4f}"


# Transposed: files as rows, operations as columns (keeps the table narrow as
# more files are added to the corpus).
file_col = max(len(short_labels[lbl]) for lbl in results)
data_col = max(
    max(len(op) for op in ops),
    max(len(fmt_cell(results[lbl].get(op))) for lbl in results for op in ops),
)

header = " " * file_col + " | " + " | ".join(f"{op:>{data_col}}" for op in ops)
print(header)
for lbl in results:
    cells = [fmt_cell(results[lbl].get(op)) for op in ops]
    print(
        f"{short_labels[lbl]:<{file_col}} | "
        + " | ".join(f"{c:>{data_col}}" for c in cells)
    )
