import logging
import time

import pytest
from util.general import TEST_FILES, get_test_json

from translator_tom import Response

pytestmark = pytest.mark.bench

LOG = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def examples() -> dict[str, str]:
    return get_test_json()


@pytest.mark.parametrize("name", [p.stem for p in TEST_FILES])
def test_convert(examples: dict[str, str], name: str) -> None:
    json_str = examples[name]
    t0 = time.perf_counter()
    LOG.info("Deserializing %s example...", name)
    Response.from_json(json_str)
    t1 = time.perf_counter()
    LOG.info("Deserialization took %s seconds.", round(t1 - t0, 6))
