"""Transform for QualifierConstraint (class → QualifierSetConstraint mapping)."""

from __future__ import annotations

from typing import Any

from translator_tom.v1_6.models.qualifier import (
    QualifierConstraint as V16QualifierConstraint,
)
from translator_tom.v2_0.convert._util import register


@register(V16QualifierConstraint, None)
def _upgrade_qualifier_constraint(data: dict[str, Any], **_: Any) -> dict[str, Any]:
    """A 1.6 QualifierConstraint (`qualifier_set` list) → a 2.0 QualifierSetConstraint.

    2.0 models a qualifier set constraint as a `{qualifier_type_id: qualifier_value}`
    mapping rather than a model, so this returns a plain dict (`target=None`).
    """
    return {
        qualifier["qualifier_type_id"]: qualifier["qualifier_value"]
        for qualifier in data["qualifier_set"]
    }
