"""Semantic-validation benchmark across every example response.

Walks `data/example_trapi/<version>/**` (default `v2_0`; pass `--version v1_6`),
deserializes each file, and runs `semantic_validate` on the resulting `Response`.
Streams per-file timings and the error/warning counts as they complete, then prints
a summary table across files at the end.

For the serdes benchmarks see `bench/test_sd_tom.py` (TOM-only, every file) and
`bench/test_sd.py` (one file per size bucket, TOM vs reasoner-pydantic).
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

VALUE_FMT = "{:>8.4f}s"


def section(title: str) -> None:
    bar = "=" * (len(title) + 2)
    print(f"\n{bar}\n {title}\n{bar}")


# --- Import ---

t0 = time.perf_counter()
_ttom = import_version(VERSION)
_validation = import_version(VERSION, "validation")
t_tom = time.perf_counter() - t0
Response = _ttom.Response
semantic_validate = _validation.semantic_validate

section("Imports")
print(f"  translator_tom.{VERSION} + validation  {VALUE_FMT.format(t_tom)}")


TEST_FILES = discover_files(CORPUS_ROOT)
print(f"\nDiscovered {len(TEST_FILES)} corpus file(s) under {CORPUS_ROOT}/")

results: dict[str, dict[str, str]] = {}


for response_path in TEST_FILES:
    label = str(response_path.relative_to(CORPUS_ROOT))
    file_results: dict[str, str] = {}
    results[label] = file_results

    t0 = time.perf_counter()
    response_json = read_corpus_file(response_path)
    t_read = time.perf_counter() - t0
    size_mb = len(response_json.encode("utf-8")) / 1024 / 1024

    section(f"{label}  ({size_mb:.2f} MB JSON, {t_read:.4f}s)")

    t0 = time.perf_counter()
    response = Response.from_json(response_json)
    t_from_json = time.perf_counter() - t0

    t0 = time.perf_counter()
    warnings, errors = semantic_validate(response)
    t_validate = time.perf_counter() - t0

    print(
        f"  from_json {VALUE_FMT.format(t_from_json)}"
        f" | validate {VALUE_FMT.format(t_validate)}"
        f" | {len(errors)} errors, {len(warnings)} warnings"
    )
    file_results["from_json"] = f"{t_from_json:.4f}s"
    file_results["validate"] = f"{t_validate:.4f}s"
    file_results["errors"] = str(len(errors))
    file_results["warnings"] = str(len(warnings))


# --- Summary ---

section("Summary")

short_labels = {
    lbl: lbl.split("/")[-1].removesuffix(".gz").removesuffix(".json")
    for lbl in results
}
ops = list(next(iter(results.values())).keys())


def fmt_cell(v: str | None) -> str:
    return "—" if v is None else v


# Transposed: files as rows, metrics as columns (keeps the table narrow as
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
