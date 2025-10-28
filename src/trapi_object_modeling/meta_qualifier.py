from __future__ import annotations

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from trapi_object_modeling.shared import CURIE


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class MetaQualifier:
    """An element describing a set of values that can be served for a given qualifier type."""

    qualifier_type_id: CURIE
    """The CURIE of the qualifier type."""

    applicable_values: list[str] | None = None
    """The list of values that are possible for this qualifier."""
