from __future__ import annotations

import itertools
from collections.abc import Iterable
from typing import Annotated, ClassVar

from pydantic import ConfigDict, Field
from typing_extensions import Self

from translator_tom.models.meta_qualifier import MetaQualifier
from translator_tom.utils.biolink import Biolink
from translator_tom.utils.object_base import TOMBase

__all__ = [
    "Qualifier",
    "QualifierConstraint",
]


class Qualifier(TOMBase):
    """An additional nuance attached to an assertion."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

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


class QualifierConstraint(TOMBase):
    """Defines a query constraint based on the qualifier_types and qualifier_values of a set of Qualifiers attached to an edge.

    For example, it can constrain a
    "ChemicalX - affects - ?Gene" query to return only edges where
    ChemicalX specifically affects the 'expression' of the Gene, by
    constraining on the qualifier_type "biolink:object_aspect_qualifier"
    with a qualifier_value of "expression".
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    qualifier_set: list[Qualifier]
    """A set of Qualifiers that serves to add nuance to a query, by constraining allowed values held by Qualifiers on queried Edges."""

    @classmethod
    def new(cls) -> Self:
        """Return an empty instance, without having to pass required containers."""
        return cls.model_construct(qualifier_set=[])

    def met_by(self, qualifiers: Iterable[Qualifier] | Iterable[MetaQualifier]) -> bool:
        """Check that the given qualifiers satisfy the constraint."""
        qualifier_pairs: list[tuple[Biolink.Qualifier, set[str]]] = [
            (
                qualifier.qualifier_type_id,
                {qualifier.qualifier_value}
                if isinstance(qualifier, Qualifier)
                else set(qualifier.applicable_values_list),
            )
            for qualifier in qualifiers
        ]

        for constr in self.qualifier_set:
            applicable_types = set(Biolink.get_descendants(constr.qualifier_type_id))
            applicable_values: set[str] | None = None
            met = False
            for qual_type, value_set in qualifier_pairs:
                if qual_type not in applicable_types:
                    continue
                if applicable_values is None:
                    # expand values once a type matches
                    applicable_values = set(
                        itertools.chain.from_iterable(
                            Biolink.get_descendant_values(t, constr.qualifier_value)
                            for t in applicable_types
                        )
                    )
                if applicable_values & value_set:
                    met = True
                    break
            if not met:
                return False

        return True

    def get_inverse(self) -> QualifierConstraint:
        """Return a (SPO) inverse of the constraint, for reversing edges."""
        new_qualifier_set = list[Qualifier]()
        for qualifier in self.qualifier_set:
            new_qualifier = qualifier.model_copy()
            if "object" in qualifier.qualifier_type_id:
                new_qualifier.qualifier_type_id = qualifier.qualifier_type_id.replace(
                    "object", "subject"
                )
            elif "subject" in qualifier.qualifier_type_id:
                new_qualifier.qualifier_type_id = qualifier.qualifier_type_id.replace(
                    "subject", "object"
                )
            elif inverse := (
                qualifier.qualifier_type_id == "biolink:qualified_predicate"
                and Biolink.get_inverse(qualifier.qualifier_value)
            ):
                new_qualifier.qualifier_value = inverse
            else:
                raise ValueError(
                    f"Cannot inverse qualifier because its value is non-inversible predicate {qualifier.qualifier_value}"
                )
            new_qualifier_set.append(new_qualifier)

        return QualifierConstraint(qualifier_set=new_qualifier_set)
