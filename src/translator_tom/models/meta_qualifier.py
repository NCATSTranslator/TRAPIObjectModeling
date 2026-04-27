from __future__ import annotations

from translator_tom.models.shared import CURIE
from translator_tom.utils.object_base import TOMBaseObject


class MetaQualifier(TOMBaseObject):
    """An element describing a set of values that can be served for a given qualifier type."""

    qualifier_type_id: CURIE
    """The CURIE of the qualifier type."""

    applicable_values: list[str] | None = None
    """The list of values that are possible for this qualifier."""

    @property
    def applicable_values_list(self) -> list[str]:
        """Get the applicable values as a guaranteed list, even if they are represented as None."""
        return self.applicable_values if self.applicable_values is not None else []
