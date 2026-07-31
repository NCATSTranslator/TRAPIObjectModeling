from __future__ import annotations

import itertools
from collections.abc import Iterable
from typing import cast

from typing_extensions import TypedDict

from translator_tom.model_dicts.meta_qualifier import MetaQualifierDict
from translator_tom.models.qualifier import Qualifier, QualifierConstraint
from translator_tom.utils.biolink import Biolink
from translator_tom.utils.dict_util_base import DictUtil

__all__ = [
    "QualifierConstraintDict",
    "QualifierConstraintDictUtil",
    "QualifierDict",
    "QualifierDictUtil",
]


class QualifierDict(TypedDict):
    qualifier_type_id: Biolink.Qualifier
    qualifier_value: str


class QualifierDictUtil(DictUtil[QualifierDict]):
    """Registration-only util for `QualifierDict`."""

    _model = Qualifier


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


class QualifierConstraintDict(TypedDict):
    qualifier_set: list[QualifierDict]


class QualifierConstraintDictUtil(DictUtil[QualifierConstraintDict]):
    """Utility methods for `QualifierConstraintDict`, mirroring those on the `QualifierConstraint` model."""

    _model = QualifierConstraint

    @staticmethod
    def new() -> QualifierConstraintDict:
        """Return an empty instance, without having to pass required containers."""
        return {"qualifier_set": []}

    @staticmethod
    def met_by(
        constraint: QualifierConstraintDict,
        qualifiers: Iterable[QualifierDict] | Iterable[MetaQualifierDict],
    ) -> bool:
        """Check that the given qualifiers satisfy the constraint."""
        qualifier_pairs: list[tuple[Biolink.Qualifier, set[str] | None]] = [
            (qualifier["qualifier_type_id"], _qualifier_values(qualifier))
            for qualifier in qualifiers
        ]

        for constr in constraint["qualifier_set"]:
            applicable_types = set(Biolink.get_descendants(constr["qualifier_type_id"]))
            allowed_values: set[str] | None = None
            met = False
            for qual_type, available_values in qualifier_pairs:
                if qual_type not in applicable_types:
                    continue
                if allowed_values is None:
                    # expand values once a type matches
                    allowed_values = set(
                        itertools.chain.from_iterable(
                            Biolink.get_descendant_values(t, constr["qualifier_value"])
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
    def set_met_by(
        constraints: list[QualifierConstraintDict],
        qualifiers: list[QualifierDict] | list[MetaQualifierDict],
    ) -> bool:
        """Check if the given set of constraints are met by the given qualifiers."""
        if len(constraints) == 0:
            return True
        elif len(qualifiers) == 0:
            return False

        return any(
            QualifierConstraintDictUtil.met_by(constraint, qualifiers)
            for constraint in constraints
        )

    @staticmethod
    def get_inverse(constraint: QualifierConstraintDict) -> QualifierConstraintDict:
        """Return a (SPO) inverse of the constraint, for reversing edges."""
        new_qualifier_set = list[QualifierDict]()
        for qualifier in constraint["qualifier_set"]:
            new_qualifier = cast("QualifierDict", {**qualifier})
            type_id = qualifier["qualifier_type_id"]
            value = qualifier["qualifier_value"]
            if "object" in type_id:
                new_qualifier["qualifier_type_id"] = type_id.replace(
                    "object", "subject"
                )
            elif "subject" in type_id:
                new_qualifier["qualifier_type_id"] = type_id.replace(
                    "subject", "object"
                )
            elif inverse := (
                type_id == "biolink:qualified_predicate" and Biolink.get_inverse(value)
            ):
                new_qualifier["qualifier_value"] = inverse
            else:
                raise ValueError(
                    f"Cannot inverse qualifier because its value is non-inversible predicate {value}"
                )
            new_qualifier_set.append(new_qualifier)

        return {"qualifier_set": new_qualifier_set}
