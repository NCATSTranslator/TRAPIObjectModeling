# Contributing

This project uses [`uv`](https://docs.astral.sh/uv/) and
[`taskipy`](https://github.com/taskipy/taskipy). Run tasks with `uv run task <name>`.

## Project structure

TOM provides multiple TRAPI versions at a time, at minimum, the latest and the previous.
Each version is a subpackage with the same internal layout:

```
src/translator_tom/
├── v<version>/      # A TRAPI version
│   ├── models/        # Pydantic models
│   ├── model_dicts/   # TypedDict models (mirrors models/)
│   ├── convert/       # Cross-version conversion (only from previous to latest)
│   └── validation/    # Semantic validation (to be removed and ported to reasoner-validator)
├── utils/             # Shared code across versions
└── scripts/           # Scripts to be used with `python -m translator_tom`
```

## Tasks

Run `uv run task -l` to list tasks, or see the `pyproject.toml` for more details.

## Before you commit

Run `uv run task fixup` and `uv run task test` and make sure they pass. `fixup` runs
lint autofix, format, typecheck, and dependency checks.

Optionally, install the pre-commit hooks with `uv run task hook`. This doesn't run
tests, so run those too.

## Running tests

- `uv run task test`: full suite with coverage.
- `uv run pytest tests/path/to/test_file.py::test_name` : a single test.

Heavy benchmarks (`@pytest.mark.bench`) are skipped unless you explicitly name their
test file in the command.

## Code style

Ruff enforces most simple style items. Some other things to keep in mind:

- When a helper serves a single class, make it a private `@staticmethod` on that class
  rather than a module-level function.
- Use Google-style docstrings. When argument and return descriptions are required, write
  them in Google style (`Args:` / `Returns:`).
