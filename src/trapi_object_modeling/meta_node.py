from __future__ import annotations

from typing import Annotated

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from trapi_object_modeling.meta_attribute import MetaAttribute


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class MetaNode:
    """Description of a node category provided by this TRAPI web service."""

    id_prefixes: Annotated[list[str], Field(min_length=1)]
    """List of CURIE prefixes for the node category that this TRAPI web service understands and accepts on the input."""

    attributes: list[MetaAttribute] | None = None
    """Node attributes provided by this TRAPI web service."""
