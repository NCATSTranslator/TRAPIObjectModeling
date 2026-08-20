"""Converter for QualifierConstraint (class → QualifierSetConstraint mapping)."""

from __future__ import annotations

from typing import Any

from translator_tom.v1_6.models.qualifier import (
    QualifierConstraint as V16QualifierConstraint,
)
from translator_tom.v2_0.convert._util import up_version


# QualifierSetConstraint is a dict type in 2.0, so this handler returns a dict.
@up_version.register(V16QualifierConstraint)  # ty: ignore[invalid-argument-type]
def _convert_qualifier_constraint(
    obj: V16QualifierConstraint, **_: Any
) -> dict[str, str]:
    """A 1.6 QualifierConstraint (`qualifier_set` list) → a 2.0 QualifierSetConstraint.

    2.0 models a qualifier set constraint as a `{qualifier_type_id: qualifier_value}`
    mapping rather than a model, so this returns a plain dict.
    """
    return {
        qualifier.qualifier_type_id: qualifier.qualifier_value
        for qualifier in obj.qualifier_set
    }
