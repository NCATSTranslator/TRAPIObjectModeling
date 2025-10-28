from __future__ import annotations

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from trapi_object_modeling.shared import CURIE


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class MetaAttribute:
    """An element describing a type of attribute that can be served."""

    attribute_type_id: CURIE
    """Type of an attribute provided by this TRAPI web service (preferably the CURIE of a Biolink association slot)."""

    attribute_source: str | None = None
    """Type of an attribute provided by this TRAPI web service (preferably the CURIE of a Biolink association slot)."""

    original_attribute_names: list[str] | None
    """Names of an the attribute as provided by the source."""

    constraint_use: bool | None = False
    """Indicates whether this attribute can be used as a query constraint."""

    constraint_name: str | None = None
    """Human-readable name or label for the constraint concept. Required whenever constraint_use is true."""
