"""Dict-util-only serdes benchmark across every example response.

The `model_dicts` twin of `bench/test_sd_tom.py`: same corpus walk and output
(default `2.0`; pass `--version 1.6`), but driving the `*DictUtil` serdes (raw
orjson/ormsgpack over the TypedDict form, no model construction) instead of the
`Response` model. Run both to see the cost the model layer adds over operating on
plain dicts.

The `+val` rows re-run the `from` path with `validate=True`, adding a pydantic
`TypeAdapter` pass over the parsed data; their `from` timing minus the plain
row's is the cost of opting into validation.
"""

import time

from utils import (
    corpus_root,
    discover_files,
    import_version,
    parse_version,
    read_corpus_file,
)

VERSION = parse_version(__doc__)
CORPUS_ROOT = corpus_root(VERSION)

LABEL_WIDTH = 12
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


def section(title: str) -> None:
    bar = "=" * (len(title) + 2)
    print(f"\n{bar}\n {title}\n{bar}")


# --- Import ---

t0 = time.perf_counter()
ResponseDictUtil = import_version(VERSION, "model_dicts").ResponseDictUtil
t_tom = time.perf_counter() - t0

section("Imports")
print(
    f"  translator_tom {VERSION} model_dicts ResponseDictUtil  {VALUE_FMT.format(t_tom)}"
)


TEST_FILES = discover_files(CORPUS_ROOT)
print(f"\nDiscovered {len(TEST_FILES)} corpus file(s) under {CORPUS_ROOT}/")

results: dict[str, dict[str, tuple[float, float]]] = {}


for response_path in TEST_FILES:
    label = str(response_path.relative_to(CORPUS_ROOT))
    file_results: dict[str, tuple[float, float]] = {}
    results[label] = file_results

    t0 = time.perf_counter()
    response_json = read_corpus_file(response_path)
    t_read = time.perf_counter() - t0
    size_mb = len(response_json.encode("utf-8")) / 1024 / 1024

    section(f"{label}  ({size_mb:.2f} MB JSON, {t_read:.4f}s)")

    t0 = time.perf_counter()
    response = ResponseDictUtil.from_json(response_json)
    t_from_json = time.perf_counter() - t0
    t0 = time.perf_counter()
    _ = ResponseDictUtil.to_json(response)
    t_to_json = time.perf_counter() - t0
    pair_row("json", t_from_json, t_to_json, file_results)

    # `to` is unaffected by validation; reuse its timing for the +val rows.
    t0 = time.perf_counter()
    _ = ResponseDictUtil.from_json(response_json, validate=True)
    t_from_json_val = time.perf_counter() - t0
    pair_row("json+val", t_from_json_val, t_to_json, file_results)

    t0 = time.perf_counter()
    response_msgpack = ResponseDictUtil.to_msgpack(response)
    t_to_mp = time.perf_counter() - t0
    t0 = time.perf_counter()
    _ = ResponseDictUtil.from_msgpack(response_msgpack)
    t_from_mp = time.perf_counter() - t0
    pair_row("msgpack", t_from_mp, t_to_mp, file_results)

    t0 = time.perf_counter()
    _ = ResponseDictUtil.from_msgpack(response_msgpack, validate=True)
    t_from_mp_val = time.perf_counter() - t0
    pair_row("msgpack+val", t_from_mp_val, t_to_mp, file_results)


# --- Summary ---

section("Summary (seconds): from / to")

short_labels = {
    lbl: lbl.split("/")[-1].removesuffix(".gz").removesuffix(".json") for lbl in results
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
