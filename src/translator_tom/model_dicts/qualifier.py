from __future__ import annotations

import itertools
from collections.abc import Iterable
from typing import cast

from typing_extensions import TypedDict

from translator_tom.model_dicts.meta_qualifier import MetaQualifierDict
from translator_tom.models.qualifier import Qualifier, QualifierSetConstraint
from translator_tom.models.shared import OBJECT_RE, SUBJECT_RE
from translator_tom.utils.biolink import Biolink
from translator_tom.utils.dict_util_base import DictUtil

__all__ = [
    "QualifierDict",
    "QualifierDictUtil",
    "QualifierSetConstraint",
]


class QualifierDict(TypedDict):
    qualifier_type_id: Biolink.Qualifier
    qualifier_value: str


def _qualifier_values(
    qualifier: QualifierDict | MetaQualifierDict,
) -> set[str] | None:
    """The values a qualifier dict contributes when matching a constraint.

    A `QualifierDict` (has `qualifier_value`) contributes its single value; a
    `MetaQualifierDict` contributes its applicable values, where None means any
    value is allowed.
    """
    if "qualifier_value" in qualifier:
        return {cast("QualifierDict", qualifier)["qualifier_value"]}
    applicable = qualifier.get("applicable_values")
    return set(applicable) if applicable is not None else None


class QualifierDictUtil(DictUtil[QualifierDict]):
    """Utility methods for `QualifierDict`, mirroring those on the `Qualifier` model."""

    _model = Qualifier

    @staticmethod
    def constraint_met_by(
        constraint: QualifierSetConstraint,
        qualifiers: Iterable[QualifierDict] | Iterable[MetaQualifierDict],
    ) -> bool:
        """Check that the given qualifiers satisfy the constraint (type/value pairs, AND-ed)."""
        qualifier_pairs: list[tuple[Biolink.Qualifier, set[str] | None]] = [
            (qualifier["qualifier_type_id"], _qualifier_values(qualifier))
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
                # available_values None means a MetaQualifier allowing all values.
                if available_values is None or allowed_values & available_values:
                    met = True
                    break
            if not met:
                return False

        return True

    @staticmethod
    def constraint_set_met_by(
        constraints: list[QualifierSetConstraint],
        qualifiers: list[QualifierDict] | list[MetaQualifierDict],
    ) -> bool:
        """Check if the given constraints are met by the given qualifiers (OR-ed)."""
        if len(constraints) == 0:
            return True
        elif len(qualifiers) == 0:
            return False

        return any(
            QualifierDictUtil.constraint_met_by(constraint, qualifiers)
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
