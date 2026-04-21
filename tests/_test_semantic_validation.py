import logging
import time

import pytest
from util.general import get_test_json

from translator_tom import Response
from translator_tom.validation import semantic_validate

TEST_EXAMPLES = get_test_json()

LOG = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "example", TEST_EXAMPLES.items(), ids=["Small", "Medium", "Large"]
)
def test_semantic_validate(example: tuple[str, str]) -> None:
    name, json_str = example
    t0 = time.perf_counter()
    LOG.info("Running semantic validation on %s example...", name)
    response = Response.from_json(json_str)
    warnings, errors = semantic_validate(response)
    t1 = time.perf_counter()
    LOG.info("Semantic validation took %s seconds.", round(t1 - t0, 6))
    LOG.info("Got %s errors and %s warnings", len(errors), len(warnings))
