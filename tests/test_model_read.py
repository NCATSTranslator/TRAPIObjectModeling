import gzip
import logging
import time
from pathlib import Path
from typing import Any

import orjson
import pytest
from pydantic import TypeAdapter

LOG = logging.getLogger(__name__)

LOG.info("Starting import of dataclass definitions")
t0 = time.perf_counter()

from trapi_object_modeling.response import Response  # noqa: E402

t1 = time.perf_counter()
LOG.info("Import conplete in %s seconds.", t1 - t0)


TEST_FILES = [
    Path("data/exampleTrapi/small.json"),
    Path("data/exampleTrapi/medium.json"),
    Path("data/exampleTrapi/large.json.gz"),
]

TEST_EXAMPLES = list[dict[str, Any]]()

for response_path in TEST_FILES:
    LOG.info(
        "Starting read of local JSON file %s of size %s MB",
        response_path,
        response_path.stat().st_size / 1024 / 1024,
    )
    t0 = time.perf_counter()

    if response_path.suffix.endswith(".gz"):
        with gzip.open(response_path, "rt", encoding="utf-8") as infile:
            response_dict = orjson.loads(infile.read())
    else:
        with response_path.open() as infile:
            response_dict = orjson.loads(infile.read())

    t1 = time.perf_counter()
    LOG.info("Read JSON file into dicts and lists in %s seconds", t1 - t0)
    LOG.info(
        "Have in hand a message with %s results",
        len(response_dict["message"]["results"]),
    )
    TEST_EXAMPLES.append(response_dict)


@pytest.fixture
def adapter() -> TypeAdapter[Response]:
    return TypeAdapter(Response)


@pytest.mark.parametrize("example", TEST_EXAMPLES, ids=["Small", "Medium", "Large"])
def test_convert(adapter: TypeAdapter[Response], example: dict[str, Any]):
    t0 = time.perf_counter()
    LOG.info("Validating using pydantic TypeAdapter...")
    adapter.validate_python(example)
    t1 = time.perf_counter()
    LOG.info("Validation took %s seconds.", t1 - t0)
