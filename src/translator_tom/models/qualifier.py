from __future__ import annotations

from collections.abc import Iterable
from typing import Annotated, Self

from pydantic import Field

from translator_tom.models.meta_qualifier import MetaQualifier
from translator_tom.utils.biolink import Biolink
from translator_tom.utils.object_base import TOMBaseObject


class Qualifier(TOMBaseObject):
    """An additional nuance attached to an assertion."""

    qualifier_type_id: Annotated[
        Biolink.Qualifier, Field(pattern=r"^biolink:[a-z][a-z_]*$")
    ]
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


class QualifierConstraint(TOMBaseObject):
    """Defines a query constraint based on the qualifier_types and qualifier_values of a set of Qualifiers attached to an edge.

    For example, it can constrain a
    "ChemicalX - affects - ?Gene" query to return only edges where
    ChemicalX specifically affects the 'expression' of the Gene, by
    constraining on the qualifier_type "biolink:object_aspect_qualifier"
    with a qualifier_value of "expression".
    """

    qualifier_set: list[Qualifier]
    """A set of Qualifiers that serves to add nuance to a query, by constraining allowed values held by Qualifiers on queried Edges."""

    def met_by(self, qualifiers: Iterable[Qualifier] | Iterable[MetaQualifier]) -> bool:
        """Check that the given qualifiers satisfy the constraint."""
        # TODO: implement (with qualifier type / value hierarchy considerations)
        raise NotImplementedError("Qualifier constraint solving not yet implemented.")

    @classmethod
    def new(cls) -> Self:
        """Return an empty instance, without having to pass required containers."""
        return cls(qualifier_set=[])
