from __future__ import annotations

from typing_extensions import TypedDict

from translator_tom.utils.biolink import Biolink

__all__ = [
    "QualifierConstraintDict",
    "QualifierDict",
]


class QualifierDict(TypedDict):
    qualifier_type_id: Biolink.Qualifier
    qualifier_value: str


class QualifierConstraintDict(TypedDict):
    qualifier_set: list[QualifierDict]
