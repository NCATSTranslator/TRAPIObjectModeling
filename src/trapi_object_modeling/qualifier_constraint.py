from __future__ import annotations

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from trapi_object_modeling.qualifier import Qualifier


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class QualifierConstraint:
    """Defines a query constraint based on the qualifier_types and qualifier_values of a set of Qualifiers attached to an edge.

    For example, it can constrain a
    "ChemicalX - affects - ?Gene" query to return only edges where
    ChemicalX specifically affects the 'expression' of the Gene, by
    constraining on the qualifier_type "biolink:object_aspect_qualifier"
    with a qualifier_value of "expression".
    """

    qualifier_set: list[Qualifier]
    """A set of Qualifiers that serves to add nuance to a query, by constraining allowed values held by Qualifiers on queried Edges."""
