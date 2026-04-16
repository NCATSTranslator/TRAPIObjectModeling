import gzip
import logging
from pathlib import Path

LOG = logging.getLogger(__name__)


def get_test_json() -> dict[str, str]:
    """Return a dictionary of label:response json"""

    test_files = [
        Path("data/exampleTrapi/small.json"),
        Path("data/exampleTrapi/medium.json"),
        Path("data/exampleTrapi/large.json.gz"),
    ]

    json_examples = list[str]()

    for response_path in test_files:
        LOG.info(
            "Read local JSON file %s of size %s MB",
            response_path,
            response_path.stat().st_size / 1024 / 1024,
        )

        if response_path.suffix.endswith(".gz"):
            with gzip.open(response_path, "rt", encoding="utf-8") as infile:
                response_json = infile.read()
        else:
            with response_path.open() as infile:
                response_json = infile.read()

        json_examples.append(response_json)

    return {
        path.stem: example
        for path, example in zip(test_files, json_examples, strict=True)
    }
