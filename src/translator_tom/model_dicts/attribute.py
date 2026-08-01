from __future__ import annotations

import re
from typing import cast

from typing_extensions import NotRequired, TypedDict

from translator_tom.model_dicts.meta_attribute import (
    MetaAttributeDict,
    MetaAttributeDictUtil,
)
from translator_tom.models.attribute import (
    _OBJECT_RE,
    _SUBJECT_RE,
    Attribute,
    AttributeConstraint,
    Operator,
)
from translator_tom.models.shared import CURIE, FastJsonValue
from translator_tom.utils.dict_util_base import DictUtil
from translator_tom.utils.hash import tomhash

__all__ = [
    "AttributeConstraintDict",
    "AttributeConstraintDictUtil",
    "AttributeDict",
    "AttributeDictUtil",
]


class AttributeDict(TypedDict):
    attribute_type_id: CURIE
    original_attribute_name: NotRequired[str | None]
    value: FastJsonValue
    value_type_id: NotRequired[CURIE | None]
    attribute_source: NotRequired[str | None]
    value_url: NotRequired[str | None]
    description: NotRequired[str | None]
    attributes: NotRequired[list[AttributeDict] | None]


class AttributeDictUtil(DictUtil[AttributeDict]):
    """Utility methods for `AttributeDict`, mirroring those on the `Attribute` model."""

    _model = Attribute

    @staticmethod
    def attributes_list(attribute: AttributeDict) -> list[AttributeDict]:
        """Get the sub-attributes as a guaranteed list, even if they are represented as None."""
        attributes = attribute.get("attributes")
        return attributes if attributes is not None else []

    @classmethod
    def hash(cls, obj: AttributeDict) -> str:
        """Hash matching `Attribute.hash` (scalar fields plus nested sub-attributes)."""
        return tomhash(
            (
                obj["attribute_type_id"],
                obj.get("original_attribute_name"),
                obj["value"],
                obj.get("value_type_id"),
                obj.get("attribute_source"),
                obj.get("value_url"),
                obj.get("description"),
                frozenset(cls.hash(a) for a in cls.attributes_list(obj)),
            )
        )

    @staticmethod
    def merge_attribute_lists(
        old: list[AttributeDict], new: list[AttributeDict]
    ) -> None:
        """Merge the new attributes into the existing attributes."""
        attrs = {AttributeDictUtil.hash(attr): attr for attr in old}
        for attr in new:
            attrs[AttributeDictUtil.hash(attr)] = attr

        old.clear()
        old.extend(attrs.values())


# Functional syntax so the `not` alias (a Python keyword) can be used as a key.
AttributeConstraintDict = TypedDict(
    "AttributeConstraintDict",
    {
        "id": CURIE,
        "name": str,
        "not": NotRequired[bool],
        "operator": Operator,
        "value": FastJsonValue,
        "unit_id": NotRequired[CURIE | None],
        "unit_name": NotRequired[str | None],
    },
)


class AttributeConstraintDictUtil(DictUtil[AttributeConstraintDict]):
    """Utility methods for `AttributeConstraintDict`, mirroring those on the `AttributeConstraint` model."""

    _model = AttributeConstraint

    @classmethod
    def hash(cls, obj: AttributeConstraintDict) -> str:
        """Hash matching `AttributeConstraint.hash` (declared scalar fields only)."""
        return tomhash(
            (
                obj["id"],
                obj["name"],
                obj.get("not", cls._default("negated")),
                obj["operator"],
                obj["value"],
                obj.get("unit_id"),
                obj.get("unit_name"),
            )
        )

    @staticmethod
    def get_inverse(constraint: AttributeConstraintDict) -> AttributeConstraintDict:
        """Return a (SPO) inverse of the constraint, for reversing edges.

        Flips subject/object for the few directional attribute types.
        """
        inverted = cast("AttributeConstraintDict", {**constraint})
        cid = constraint["id"]
        name = constraint["name"]
        if _OBJECT_RE.search(cid):
            inverted["id"] = _OBJECT_RE.sub("subject", cid)
            inverted["name"] = _OBJECT_RE.sub("subject", name)
        elif _SUBJECT_RE.search(cid):
            inverted["id"] = _SUBJECT_RE.sub("object", cid)
            inverted["name"] = _SUBJECT_RE.sub("object", name)
        return inverted

    @staticmethod
    def met_by(
        constraint: AttributeConstraintDict,
        attribute: AttributeDict | MetaAttributeDict,
    ) -> bool:
        """Check if the given attribute satisfies the constraint."""
        # A MetaAttributeDict has no `value` key (required on an AttributeDict).
        if "value" not in attribute:
            return (
                constraint["id"] == attribute["attribute_type_id"]
                and attribute.get(
                    "constraint_use", MetaAttributeDictUtil._default("constraint_use")
                )
                is not False
            )

        attr = cast("AttributeDict", attribute)
        if constraint["id"] != attr["attribute_type_id"]:
            return False

        operator = constraint["operator"]
        con_value = constraint["value"]
        if operator == "===":
            result = attr["value"] == con_value
        else:
            attr_vals = (
                attr["value"] if isinstance(attr["value"], list) else [attr["value"]]
            )
            con_vals = con_value if isinstance(con_value, list) else [con_value]

            match operator:
                case "==":
                    result = any(av == cv for av in attr_vals for cv in con_vals)
                case ">" | "<":
                    result = any(
                        (av > cv if operator == ">" else av < cv)
                        for av in attr_vals
                        for cv in con_vals
                        if isinstance(av, int | float) and isinstance(cv, int | float)
                    )
                case "matches":
                    result = any(
                        bool(re.search(cv, av))
                        for cv in con_vals
                        for av in attr_vals
                        if isinstance(cv, str) and isinstance(av, str)
                    )

        return (
            not result
            if constraint.get("not", AttributeConstraintDictUtil._default("negated"))
            else result
        )

    @staticmethod
    def set_met_by(
        constraints: list[AttributeConstraintDict],
        attributes: list[AttributeDict] | list[MetaAttributeDict],
    ) -> bool:
        """Check if the given set of constraints are met by the given attributes."""
        if len(constraints) == 0:
            return True
        elif len(attributes) == 0:
            return False

        attrs_by_type: dict[CURIE, list[AttributeDict | MetaAttributeDict]] = {}
        for attr in attributes:
            attrs_by_type.setdefault(attr["attribute_type_id"], []).append(attr)
        return all(
            any(
                AttributeConstraintDictUtil.met_by(c, attr)
                for attr in attrs_by_type.get(c["id"], [])
            )
            for c in constraints
        )
