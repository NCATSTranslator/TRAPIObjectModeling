from __future__ import annotations

from typing import override

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass
from stablehash import stablehash

from trapi_object_modeling.models.shared import CURIE
from trapi_object_modeling.utils.object_base import TOMBaseObject


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class MetaAttribute(TOMBaseObject):
    """An element describing a type of attribute that can be served."""

    attribute_type_id: CURIE
    """Type of an attribute provided by this TRAPI web service (preferably the CURIE of a Biolink association slot)."""

    attribute_source: str | None = None
    """Source of an attribute provided by this TRAPI web service."""

    original_attribute_names: list[str] | None
    """Names of an the attribute as provided by the source."""

    constraint_use: bool | None = False
    """Indicates whether this attribute can be used as a query constraint."""

    constraint_name: str | None = None
    """Human-readable name or label for the constraint concept. Required whenever constraint_use is true."""

    @property
    def original_attribute_names_list(self) -> list[str]:
        """Get the original attribute names as a guaranteed list, even if they are represented as None."""
        return (
            self.original_attribute_names
            if self.original_attribute_names is not None
            else []
        )

    @override
    def hash(self) -> str:
        return stablehash(
            (self.attribute_type_id, self.attribute_source, self.constraint_use)
        ).hexdigest()
