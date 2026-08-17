"""Sweep: every declared model field carries its docstring as a schema description.

`use_attribute_docstrings=True` (on `TOMBase.model_config`) promotes each field's
attribute docstring to its `FieldInfo.description`, so `model_json_schema()` output
carries the text. This suite verifies that promotion across every exported model — both
on the `FieldInfo` and in the generated schema — so new models and any config-inheritance
regression are caught automatically.
"""

from __future__ import annotations

from typing import Any

import pytest

from _sweep_helpers import MODELS

# Fields whose attribute docstring is intentionally still missing, pending author review.
# Format: (ModelName, field_name). Remove entries as docstrings are supplied.
KNOWN_MISSING: set[tuple[str, str]] = set()

_MODEL_IDS = [m.__name__ for m in MODELS]


def _schema_key(field: Any, name: str) -> str:
    """The property key used in the by-alias JSON schema (aliases win)."""
    return field.serialization_alias or field.alias or name


def _root_props(model: type) -> dict[str, Any]:
    """Own-field property block, following the root `$ref` self-referential models emit."""
    schema = model.model_json_schema()
    if "properties" in schema:
        return schema["properties"]
    return schema.get("$defs", {}).get(model.__name__, {}).get("properties", {})


@pytest.mark.parametrize("model", MODELS, ids=_MODEL_IDS)
def test_every_field_has_description(model: type) -> None:
    missing = [
        name
        for name, field in model.model_fields.items()
        if (model.__name__, name) not in KNOWN_MISSING
        and not (isinstance(field.description, str) and field.description.strip())
    ]
    assert not missing, f"{model.__name__} fields lack a description: {missing}"


@pytest.mark.parametrize("model", MODELS, ids=_MODEL_IDS)
def test_descriptions_present_in_schema(model: type) -> None:
    props = _root_props(model)
    missing = [
        name
        for name, field in model.model_fields.items()
        if (model.__name__, name) not in KNOWN_MISSING
        and field.description
        and not props.get(_schema_key(field, name), {}).get("description")
    ]
    assert not missing, f"{model.__name__} schema properties missing description: {missing}"
