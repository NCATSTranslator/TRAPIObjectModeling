import logging
import time

import pytest
from util.general import get_test_json

from translator_tom import Response

TEST_EXAMPLES = get_test_json()

LOG = logging.getLogger(__name__)


@pytest.mark.parametrize("example", TEST_EXAMPLES.items(), ids=["Small", "Medium", "Large"])
def test_convert(example: tuple[str, str]):
    name, json_str = example
    t0 = time.perf_counter()
    LOG.info("Deserializing %s example...", name)
    Response.from_json(json_str)
    t1 = time.perf_counter()
    LOG.info("Deserialization took %s seconds.", round(t1 - t0, 6))
