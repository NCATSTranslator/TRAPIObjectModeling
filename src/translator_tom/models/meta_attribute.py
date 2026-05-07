from __future__ import annotations

from typing import Annotated

from pydantic import Field
from typing_extensions import override

from translator_tom.models.shared import CURIE
from translator_tom.utils.hash import tomhash
from translator_tom.utils.object_base import TOMBase

__all__ = ["MetaAttribute"]


class MetaAttribute(TOMBase):
    """An element describing a type of attribute that can be served."""

    attribute_type_id: CURIE
    """Type of an attribute provided by this TRAPI web service (preferably the CURIE of a Biolink association slot)."""

    attribute_source: str | None = None
    """Source of an attribute provided by this TRAPI web service."""

    original_attribute_names: Annotated[list[str] | None, Field(min_length=1)] = None
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
        return tomhash(
            (self.attribute_type_id, self.attribute_source, self.constraint_use)
        )

    @staticmethod
    def merge_attribute_lists(
        old: list[MetaAttribute], new: list[MetaAttribute]
    ) -> None:
        """Merge the new attributes into the existing attributes."""
        attrs = {attr.hash(): attr for attr in old}
        for attr in new:
            attrs[attr.hash()] = attr

        old.clear()
        old.extend(attrs.values())
