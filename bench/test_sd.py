"""Quick serdes benchmark: one file per size bucket, comparing TOM vs reasoner-pydantic.

Runs against `data/example_trapi/<version>/` (default `v2_0`; pass `--version v1_6`).
Streams per-file timings in an aligned format as they complete, then prints a
summary table across files at the end.
"""

import time

import orjson
from pydantic import TypeAdapter

from utils import corpus_root, import_version, parse_version, read_corpus_file

VERSION = parse_version(__doc__)
CORPUS_ROOT = corpus_root(VERSION)

LABEL_WIDTH = 23
VALUE_FMT = "{:>8.4f}s"


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


def skipped(label: str, reason: str, bucket: dict[str, tuple[float, float]]) -> None:
    """Record a SKIPPED pair and print a single notice line."""
    print(f"  {label:<{LABEL_WIDTH}} SKIPPED ({reason})")
    bucket[label] = (float("nan"), float("nan"))


def section(title: str) -> None:
    bar = "=" * (len(title) + 2)
    print(f"\n{bar}\n {title}\n{bar}")


# --- Imports ---

t0 = time.perf_counter()
Response = import_version(VERSION).Response
t_tom = time.perf_counter() - t0

t0 = time.perf_counter()
from reasoner_pydantic import Response as RPResponse  # noqa: E402

t_rp = time.perf_counter() - t0

section("Imports")
print(f"  {f'translator_tom.{VERSION}':<{LABEL_WIDTH}} {VALUE_FMT.format(t_tom)}")
print(f"  {'reasoner-pydantic':<{LABEL_WIDTH}} {VALUE_FMT.format(t_rp)}")


# One representative file per size bucket. To benchmark every file, see
# `bench/test_sd_tom.py`.
TEST_FILES = [
    CORPUS_ROOT / "10mb/pathfinder.json",
    CORPUS_ROOT / "50mb/lookup.json",
    CORPUS_ROOT / "250mb/attribute-heavy.json.gz",
]

results: dict[str, dict[str, tuple[float, float]]] = {}
adapter = TypeAdapter(Response)


for response_path in TEST_FILES:
    label = str(response_path.relative_to(CORPUS_ROOT))
    file_results: dict[str, tuple[float, float]] = {}
    results[label] = file_results

    # --- Read ---
    t0 = time.perf_counter()
    response_json = read_corpus_file(response_path)
    t_read = time.perf_counter() - t0
    size_mb = len(response_json.encode("utf-8")) / 1024 / 1024

    section(f"{label}  ({size_mb:.2f} MB JSON, {t_read:.4f}s)")

    # --- orjson ---
    t0 = time.perf_counter()
    response_dict = orjson.loads(response_json)
    t_loads = time.perf_counter() - t0
    t0 = time.perf_counter()
    _ = orjson.dumps(response_dict)
    t_dumps = time.perf_counter() - t0
    pair_row("orjson", t_loads, t_dumps, file_results)

    # --- adapter (python: dict <-> model) ---
    t0 = time.perf_counter()
    response = adapter.validate_python(response_dict)
    t_vp = time.perf_counter() - t0
    t0 = time.perf_counter()
    _ = adapter.dump_python(response)
    t_dp = time.perf_counter() - t0
    pair_row("adapter.python", t_vp, t_dp, file_results)

    # Combined dict-based pipeline (alternative to adapter.json single-pass).
    pair_row(
        "orjson + adapter.python", t_loads + t_vp, t_dp + t_dumps, file_results
    )

    # --- adapter (json: bytes <-> model) ---
    t0 = time.perf_counter()
    response = adapter.validate_json(response_json)
    t_vj = time.perf_counter() - t0
    t0 = time.perf_counter()
    _ = adapter.dump_json(response)
    t_dj = time.perf_counter() - t0
    pair_row("adapter.json", t_vj, t_dj, file_results)

    # --- Response.json (TOMBase convenience methods) ---
    t0 = time.perf_counter()
    response = Response.from_json(response_json)
    t_fj = time.perf_counter() - t0
    t0 = time.perf_counter()
    _ = response.to_json()
    t_tj = time.perf_counter() - t0
    pair_row("Response.json", t_fj, t_tj, file_results)

    # --- Response.msgpack ---
    t0 = time.perf_counter()
    response_msgpack = response.to_msgpack()
    t_to_mp = time.perf_counter() - t0
    t0 = time.perf_counter()
    _ = Response.from_msgpack(response_msgpack)
    t_from_mp = time.perf_counter() - t0
    pair_row("Response.msgpack", t_from_mp, t_to_mp, file_results)

    # --- Reasoner-Pydantic ---
    try:
        t0 = time.perf_counter()
        rp_response = RPResponse.model_validate_json(response_json)
        t_rp_des = time.perf_counter() - t0
        t0 = time.perf_counter()
        _ = rp_response.model_dump_json()
        t_rp_ser = time.perf_counter() - t0
        pair_row("reasoner-pydantic", t_rp_des, t_rp_ser, file_results)
    except Exception as e:  # noqa: BLE001
        # RP is stricter than TOM about null-vs-absent; some real corpora are
        # accepted by TOM but rejected by RP. Skip rather than abort.
        skipped("reasoner-pydantic", str(e).splitlines()[0], file_results)


# --- Summary ---

section("Summary (seconds): from / to")

short_labels = {
    lbl: lbl.split("/")[-1].removesuffix(".gz").removesuffix(".json")
    for lbl in results
}
ops = list(next(iter(results.values())).keys())


def fmt_cell(v: tuple[float, float] | None) -> str:
    if v is None or v[0] != v[0]:  # missing or NaN
        return "—"
    return f"{v[0]:.4f} / {v[1]:.4f}"


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
