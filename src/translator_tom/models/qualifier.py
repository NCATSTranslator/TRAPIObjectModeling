from __future__ import annotations

from typing import Annotated

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from translator_tom.models.shared import CURIE
from translator_tom.utils.object_base import TOMBaseObject


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class Qualifier(TOMBaseObject):
    """An additional nuance attached to an assertion."""

    qualifier_type_id: Annotated[CURIE, Field(pattern=r"^biolink:[a-z][a-z_]*$")]
    """CURIE for a Biolink 'qualifier' association slot, generally taken from Biolink association slots designated for this purpose (that is, association slots with names ending in 'qualifier') e.g. biolink:subject_aspect_qualifier,  biolink:subject_direction_qualifier, biolink:object_aspect_qualifier, etc. Such qualifiers are used to elaborate a second layer of meaning of a knowledge graph edge.

    Available qualifiers are edge properties in the Biolink Model (see
    https://biolink.github.io/biolink-model/docs/edge_properties.html)
    which have slot names with the suffix string 'qualifier'.
    """

    qualifier_value: str
    """The value associated with the type of the qualifier, drawn from a set of controlled values by the type as specified in the Biolink model (e.g. 'expression' or 'abundance' for the qualifier type 'biolink:subject_aspect_qualifier', etc).

    The enumeration of qualifier values for a given qualifier
    type is generally going to be constrained by the category
    of edge (i.e. biolink:Association subtype) of the (Q)Edge.
    """
