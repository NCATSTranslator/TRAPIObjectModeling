import gzip
import time
from pathlib import Path

import orjson
from pydantic import TypeAdapter

print("Starting import of dataclass definitions")
t0 = time.perf_counter()

from trapi_object_modeling.response import Response  # noqa: E402

t1 = time.perf_counter()
print(f"Import complete in {t1 - t0} seconds.")


TEST_FILES = [
    Path("data/exampleTrapi/small.json"),
    Path("data/exampleTrapi/medium.json"),
    Path("data/exampleTrapi/large.json.gz"),
]


for response_path in TEST_FILES:
    print(
        f"Starting read of local JSON file {response_path} of size {response_path.stat().st_size / 1024 / 1024} MB"
    )
    t0 = time.perf_counter()

    if response_path.suffix.endswith(".gz"):
        with gzip.open(response_path, "rt", encoding="utf-8") as infile:
            response_dict = orjson.loads(infile.read())
    else:
        with response_path.open() as infile:
            response_dict = orjson.loads(infile.read())

    t1 = time.perf_counter()
    print(f"Read JSON file into dicts and lists in {t1 - t0} seconds")
    print(
        "Have in hand a message with {} results".format(
            len(response_dict["message"]["results"]),
        )
    )

    adapter = TypeAdapter(Response)

    t0 = time.perf_counter()
    print("Validating using pydantic TypeAdapter...")
    response = adapter.validate_python(response_dict)
    t1 = time.perf_counter()
    print(f"Validation took {t1 - t0} seconds.")
