import logging
import time

import pytest
from util.general import TEST_FILES, get_test_json

from translator_tom import Response
from translator_tom.validation import semantic_validate

pytestmark = pytest.mark.bench

LOG = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def examples() -> dict[str, str]:
    return get_test_json()


@pytest.mark.parametrize("name", [p.stem for p in TEST_FILES])
def test_semantic_validate(examples: dict[str, str], name: str) -> None:
    json_str = examples[name]
    t0 = time.perf_counter()
    LOG.info("Running semantic validation on %s example...", name)
    response = Response.from_json(json_str)
    warnings, errors = semantic_validate(response)
    t1 = time.perf_counter()
    LOG.info("Semantic validation took %s seconds.", round(t1 - t0, 6))
    LOG.info("Got %s errors and %s warnings", len(errors), len(warnings))
