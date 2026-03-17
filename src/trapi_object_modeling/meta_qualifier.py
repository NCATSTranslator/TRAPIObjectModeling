from __future__ import annotations

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from trapi_object_modeling.shared import CURIE
from trapi_object_modeling.utils.object_base import TOMBaseObject


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class MetaQualifier(TOMBaseObject):
    """An element describing a set of values that can be served for a given qualifier type."""

    qualifier_type_id: CURIE
    """The CURIE of the qualifier type."""

    applicable_values: list[str] | None = None
    """The list of values that are possible for this qualifier."""
