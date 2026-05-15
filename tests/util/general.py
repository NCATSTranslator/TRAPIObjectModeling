import gzip
import logging
from pathlib import Path

LOG = logging.getLogger(__name__)

# Enumerated as a module constant so callers (e.g. pytest parametrize) can
# discover the example set without paying the load cost.
TEST_FILES: list[Path] = [
    Path("data/example_trapi/10mb/pathfinder.json"),
    # Path("data/example_trapi/10mb/log-heavy.json"),
    # Path("data/example_trapi/50mb/lookup.json"),
    Path("data/example_trapi/50mb/result-heavy.json"),
    Path("data/example_trapi/250mb/attribute-heavy.json.gz"),
]


def _read(path: Path) -> str:
    LOG.info(
        "Read local JSON file %s of size %s MB",
        path,
        path.stat().st_size / 1024 / 1024,
    )
    if path.suffix.endswith(".gz"):
        with gzip.open(path, "rt", encoding="utf-8") as infile:
            return infile.read()
    with path.open() as infile:
        return infile.read()


def get_test_json() -> dict[str, str]:
    """Return a dictionary of label:response json."""
    return {path.stem: _read(path) for path in TEST_FILES}
