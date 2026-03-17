import gzip
import time
from pathlib import Path

import orjson
from pydantic import TypeAdapter

t0 = time.perf_counter()
from trapi_object_modeling import Response

t1 = time.perf_counter()

print(f"Import Response model in {(t1 - t0):.6f}s.")


TEST_FILES = [
    Path("data/exampleTrapi/small.json"),
    Path("data/exampleTrapi/medium.json"),
    Path("data/exampleTrapi/large.json.gz"),
]


for response_path in TEST_FILES:
    print()
    t0 = time.perf_counter()

    if response_path.suffix.endswith(".gz"):
        with gzip.open(response_path, "rt", encoding="utf-8") as infile:
            response_json = infile.read()
    else:
        with response_path.open() as infile:
            response_json = infile.read()

    t1 = time.perf_counter()
    print(
        f"Read {response_path} to {(len(response_json.encode('utf-8')) / 1024 / 1024):.6f} MB JSON str in {(t1 - t0):.6}s."
    )

    adapter = TypeAdapter(Response)

    t0 = time.perf_counter()
    response_dict = orjson.loads(response_json)
    t1 = time.perf_counter()

    t2 = time.perf_counter()
    response = adapter.validate_python(response_dict)
    t3 = time.perf_counter()
    print(
        f"Parse {(t1 - t0):.6f}s / Validate {(t3 - t2):.6f}s / Total {((t1 - t0) + (t3 - t2)):.6f}s, got {len(response.message.results or [])} result(s)."
    )

    t0 = time.perf_counter()
    response = adapter.validate_json(response_json)
    t1 = time.perf_counter()

    t2 = time.perf_counter()
    response = Response.from_json(response_json)
    t3 = time.perf_counter()
    print(f"Direct Deserialize: Pydantic {(t1 - t0):.6f} / Class {(t3 - t2):.6f}s.")

    t0 = time.perf_counter()
    dump = adapter.dump_python(response)
    t1 = time.perf_counter()

    t2 = time.perf_counter()
    json = orjson.dumps(dump)
    t3 = time.perf_counter()
    print(
        f"Dump {(t1 - t0):.6f}s / Serialize {(t3 - t2):.6f}s / Total {((t1 - t0) + (t3 - t2)):.6f}s."
    )

    t0 = time.perf_counter()
    dump = adapter.dump_json(response)
    t1 = time.perf_counter()

    t2 = time.perf_counter()
    response = Response.to_json(response)
    t3 = time.perf_counter()
    print(f"Direct Serialize: Pydantic {(t1 - t0):.6f}s / Class {(t3 - t2):.6f}s.")
