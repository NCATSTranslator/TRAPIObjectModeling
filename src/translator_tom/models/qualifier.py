from __future__ import annotations

import itertools
from collections.abc import Iterable
from typing import Annotated, ClassVar

from pydantic import ConfigDict, Field

from translator_tom.models.meta_qualifier import MetaQualifier
from translator_tom.models.shared import OBJECT_RE, SUBJECT_RE
from translator_tom.utils.biolink import Biolink
from translator_tom.utils.object_base import TOMBase

__all__ = [
    "Qualifier",
    "QualifierSetConstraint",
]


class Qualifier(TOMBase):
    """An additional nuance attached to an assertion."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    qualifier_type_id: Biolink.Qualifier
    """CURIE for a Biolink 'qualifier' association slot, generally taken from Biolink association slots designated for this purpose e.g. biolink:subject_aspect_qualifier, biolink:subject_direction_qualifier, biolink:object_aspect_qualifier, etc.

    Such qualifiers are used to elaborate a second layer of meaning of a
    knowledge graph edge. Available qualifiers can be found at
    https://biolink.github.io/biolink-model/qualifiers.html, which mostly
    have slot names with the suffix string 'qualifier'.
    """

    qualifier_value: str
    """The value associated with the type of the qualifier, drawn from a set of controlled values by the type as specified in the Biolink model (e.g. 'expression' or 'abundance' for the qualifier type 'biolink:subject_aspect_qualifier', etc).

    The enumeration of qualifier values for a given qualifier
    type is generally constrained by the category of the edge
    (i.e. biolink:Association subtype).
    """

    @staticmethod
    def constraint_met_by(
        constraint: QualifierSetConstraint,
        qualifiers: Iterable[Qualifier] | Iterable[MetaQualifier],
    ) -> bool:
        """Check that the given qualifiers satisfy the constraint (a set of qualifier type/value pairs, AND-ed)."""
        qualifier_pairs: list[tuple[Biolink.Qualifier, set[str] | None]] = [
            (
                qualifier.qualifier_type_id,
                {qualifier.qualifier_value}
                if isinstance(qualifier, Qualifier)
                else (
                    set(qualifier.applicable_values)
                    if qualifier.applicable_values is not None
                    else None
                ),
            )
            for qualifier in qualifiers
        ]

        for constr_type_id, constr_value in constraint.items():
            applicable_types = set(Biolink.get_descendants(constr_type_id))
            allowed_values: set[str] | None = None
            met = False
            for qual_type, available_values in qualifier_pairs:
                if qual_type not in applicable_types:
                    continue
                if allowed_values is None:
                    # expand values once a type matches
                    allowed_values = set(
                        itertools.chain.from_iterable(
                            Biolink.get_descendant_qualifier_values(t, constr_value)
                            for t in applicable_types
                        )
                    )
                # If available_values is None, we're dealing with a MetaQualifier that
                # set applicable_values to None, which means all are allowed.
                if available_values is None or allowed_values & available_values:
                    met = True
                    break
            if not met:
                return False

        return True

    @staticmethod
    def constraint_set_met_by(
        constraints: list[QualifierSetConstraint],
        qualifiers: list[Qualifier] | list[MetaQualifier],
    ) -> bool:
        """Check if the given constraints are met by the given qualifiers (constraints are OR-ed)."""
        if len(constraints) == 0:
            return True
        elif len(qualifiers) == 0:
            return False

        return any(
            Qualifier.constraint_met_by(constraint, qualifiers)
            for constraint in constraints
        )

    @staticmethod
    def get_constraint_inverse(
        constraint: QualifierSetConstraint,
    ) -> QualifierSetConstraint:
        """Return a (SPO) inverse of the constraint, for reversing edges."""
        inverse = dict[Biolink.Qualifier, str]()
        for type_id, value in constraint.items():
            if OBJECT_RE.search(type_id):
                inverse[OBJECT_RE.sub("subject", type_id)] = value
            elif SUBJECT_RE.search(type_id):
                inverse[SUBJECT_RE.sub("object", type_id)] = value
            elif type_id == "biolink:qualified_predicate":
                inverse_value = Biolink.get_inverse(value)
                if not inverse_value:
                    raise ValueError(
                        f"Cannot invert qualified_predicate: no inverse for predicate {value}"
                    )
                inverse[type_id] = inverse_value
            else:
                raise ValueError(f"Cannot invert qualifier of type {type_id}")
        return inverse


QualifierSetConstraint = Annotated[dict[Biolink.Qualifier, str], Field(min_length=1)]
"""A constraint on the qualifiers of a bound Edge (types and values).

A given key-value pair defines the required qualifier_type_id
and qualifier_value of one Qualifier, respectively.
For example, a QualifierSetConstraint can constrain a
"ChemicalX - affects - ?Gene" query to return only edges where
ChemicalX specifically affects the 'expression' of the Gene, by
constraining on the qualifier_type "biolink:object_aspect_qualifier"
with a qualifier_value of "expression".
Multiple type-value pairs have an AND relationship.
"""
