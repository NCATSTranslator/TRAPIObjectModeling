"""Pytest configuration for the TOM test suite.

Tests marked `bench` are skipped unless their containing file is named
explicitly on the pytest command line. This lets `pytest` (or any directory
sweep like `pytest tests/`) stay fast, while
`pytest tests/test_models/test_model_read.py` still runs them.
"""

from __future__ import annotations

import pytest


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    invocation_args = config.invocation_params.args

    def explicitly_invoked(item: pytest.Item) -> bool:
        # item.path is the absolute path to the test file
        for arg in invocation_args:
            target = arg.split("::", 1)[0]
            if not target:
                continue
            if str(item.path).endswith(target) or target.endswith(item.path.name):
                return True
        return False

    skip_bench = pytest.mark.skip(
        reason="bench test — run the file directly (`pytest <path>`) to invoke"
    )
    for item in items:
        if "bench" in item.keywords and not explicitly_invoked(item):
            item.add_marker(skip_bench)
