from __future__ import annotations

from pydantic import JsonValue
from typing_extensions import NotRequired, TypedDict

from translator_tom.models.attribute import Operator
from translator_tom.models.shared import CURIE

__all__ = [
    "AttributeConstraintDict",
    "AttributeDict",
]


class AttributeDict(TypedDict):
    attribute_type_id: CURIE
    original_attribute_name: NotRequired[str | None]
    value: JsonValue
    value_type_id: NotRequired[CURIE | None]
    attribute_source: NotRequired[str | None]
    value_url: NotRequired[str | None]
    description: NotRequired[str | None]
    attributes: NotRequired[list[AttributeDict] | None]


# Functional syntax so the `not` alias (a Python keyword) can be used as a key.
AttributeConstraintDict = TypedDict(
    "AttributeConstraintDict",
    {
        "id": CURIE,
        "name": str,
        "not": NotRequired[bool | None],
        "operator": Operator,
        "value": JsonValue,
        "unit_id": NotRequired[CURIE | None],
        "unit_name": NotRequired[str | None],
    },
)
