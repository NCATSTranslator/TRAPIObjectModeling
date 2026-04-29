from __future__ import annotations

import re
from enum import Enum
from typing import Annotated, ClassVar, Literal, override

from pydantic import ConfigDict, Field

from translator_tom.models.meta_attribute import MetaAttribute
from translator_tom.models.shared import CURIE, FastJsonValue
from translator_tom.utils.hash import tomhash
from translator_tom.utils.object_base import TOMBaseObject


class OperatorEnum(str, Enum):
    """Relationship between the database value and the constraint value for the specified id.

    For every operator except === (EQ_STRICT), if the value of the compared attribute
    is a list, then comparisons are performed between each of the constraint values and
    each of the attribute values, and any one true evaluation counts as an overall true
    (e.g., [1,2,3] == [6,7,2] is true).
    """

    EQ = "=="
    """Equals.

    If value is a list type, then at least one evaluation must be true
    (equivalent to OR). This means that the == operator with a list acts like a SQL 'IN'
    clause. The == operator is therefore a broad interpretation of inclusion.

    The 'not' property negates the operator such that not and == means 'not equal to'
    (or 'not in' for a list).

    The '==' operator SHOULD NOT be used in a manner that describes an "is a" subclass
    relationship for the parent QNode.
    """

    EQ_STRICT = "==="
    """Strict equality.

    The '===' operator requires that the constraint value and the attribute value be
    the same data type, length, content, and order (e.g. only [1,2,3] === [1,2,3]).

    The 'not' property negates the operator such that not and === means the match
    between the constraint and attribute values are not exact.
    """

    GT = ">"
    """Greater than.

    The 'not' property negates the operator such that not > means <=
    (less than or equal to).
    """
    LT = "<"
    """Less than.

    The 'not' property negates the operator such that not < means >=
    (greater than or equal to).
    """

    MATCHES = "matches"
    """Regex match.

    The 'matches' operator indicates that the value is a regular expression to be
    evaluated.

    The 'not' property negates the operator such that not matches means does not match
    the provided regex.
    """


Operator = Literal["==", "===", ">", "<", "matches"]


class Attribute(TOMBaseObject):
    """Generic attribute for a node or an edge that expands the key-value pair concept by including fields for additional metadata.

    These fields can be used to describe the source of the statement made in a key-value
    pair of the attribute object, or describe the attribute's value itself
    including its semantic type, or a url providing additional information
    about it. An attribute may be further qualified with sub-attributes
    (for example to provide confidence intervals on a value).
    """

    attribute_type_id: CURIE
    """The 'key' of the attribute object, holding a CURIE of an ontology property defining the attribute (preferably the CURIE of a Biolink association slot).

    This property captures the relationship asserted to hold between the value of the attribute, and the node
    or edge from  which it hangs. For example, that a value of
    '0.000153' represents a p-value supporting an edge, or that
    a value of 'ChEMBL' represents the original source of the knowledge
    expressed in the edge.
    """

    original_attribute_name: str | None = None
    """The term used by the original source of an attribute to describe the meaning or significance of the value it captures.

    This may be a column name in a source tsv file, or a key in a source json
    document for the field in the data that held the attribute's
    value. Capturing this information  where possible lets us preserve
    what the original source said. Note that the data type is string'
    but the contents of the field could also be a CURIE of a third
    party ontology term.
    """

    value: FastJsonValue
    """Value of the attribute. May be any data type, including a list."""

    value_type_id: CURIE | None = None
    """CURIE describing the semantic type of an  attribute's value.

    Use a Biolink class if possible, otherwise a term from an external
    ontology. If a suitable CURIE/identifier does not exist, enter a
    descriptive phrase here and submit the new type for consideration
    by the appropriate authority.
    """

    attribute_source: str | None = None
    """The source of the core assertion made by the key-value pair of an attribute object.

    Use a CURIE or namespace designator for this resource where possible.
    """

    value_url: str | None = None
    """Human-consumable URL linking to a web document that provides additional information about an attribute's value (not the node or the edge fom which it hangs)."""

    description: str | None = None
    """Human-readable description for the attribute and its value."""

    attributes: list[Attribute] | None = None
    """A list of attributes providing further information about the parent attribute (for example to provide provenance information about the parent attribute)."""

    @property
    def attributes_list(self) -> list[Attribute]:
        """Get the attributes as a guaranteed list, even if they are represented as None."""
        return self.attributes if self.attributes is not None else []

    @override
    def hash(self) -> str:
        # Skip more expensive default hash traversal
        # (No TOMBaseObject in FastJsonValue)
        return tomhash(
            (
                self.attribute_type_id,
                self.original_attribute_name,
                self.value,
                self.value_type_id,
                self.attribute_source,
                self.value_url,
                self.description,
                frozenset(a.hash() for a in self.attributes_list),
            )
        )

    @staticmethod
    def merge_attribute_lists(old: list[Attribute], new: list[Attribute]) -> None:
        """Merge the new attributes into the existing attributes."""
        attrs = {attr.hash(): attr for attr in old}
        for attr in new:
            attrs[attr.hash()] = attr

        old.clear()
        old.extend(attrs.values())


class AttributeConstraint(TOMBaseObject):
    """Generic query constraint for a query node or query edge."""

    # `negated` serializes as "not" (reserved word) via Field(alias="not").
    model_config: ClassVar[ConfigDict] = ConfigDict(serialize_by_alias=True)

    id: CURIE
    """CURIE of the concept being constrained.

    For properties defined by the Biolink model this SHOULD be a biolink CURIE.
    otherwise, if possible, from the EDAM ontology. If a suitable
    CURIE does not exist, enter a descriptive phrase here and
    submit the new type for consideration by the appropriate
    authority.
    """

    name: str
    """Human-readable name or label for the constraint concept.

    If appropriate, it SHOULD be the term name of the CURIE used
    as the 'id'. This is redundant but required for human
    readability.
    """

    negated: Annotated[bool | None, Field(alias="not")] = False
    """Negate the operator."""

    operator: Operator
    """Relationship between the database value and the constraint value for the specified id.

    The operators ==, >, and < mean is equal to, is greater than, and is less than,
    respectively. The 'matches' operator indicates that the value
    is a regular expression to be evaluated. If value is a list type,
    then at least one evaluation must be true (equivalent to OR).
    This means that the == operator with a list acts like a SQL 'IN'
    clause. If the value of the compared attribute is a list, then
    comparisons are performed between each of the constraint values
    and each of the attribute values, and any one true evaluation
    counts as an overall true (e.g., [1,2,3] == [6,7,2] is true).
    The == operator is therefore a broad interpretation of inclusion.
    The '===' operator requires that the constraint value and
    the attribute value be the same data type, length,
    content, and order (e.g. only [1,2,3] === [1,2,3]).
    The 'not' property negates the operator such that not
    and == means 'not equal to' (or 'not in' for a list), and not >
    means <=, and not < means >=, not matches means does not
    match, and not === means the match between the constraint
    and attribute values are not exact.
    The '==' operator SHOULD NOT be used in a manner that
    describes an "is a" subclass relationship for the parent QNode.
    """

    value: FastJsonValue
    """Value of the attribute.

    May be any data type, including a list.
    If the value is a list and there are multiple items, at least one
    comparison must be true (equivalent to OR) unless the '==='
    operator is used. If 'value' is of data
    type 'object', the keys of the object MAY be treated as a list.
    A 'list' data type paired with the '>' or '<' operators will
    encode extraneous comparisons, but this is permitted as it is in
    SQL and other languages.
    """

    unit_id: CURIE | None = None
    """CURIE of the units of the value or list of values in the 'value' property.

    The Units of Measurement Ontology (UO) should be used
    if possible. The unit_id MUST be provided for (lists of)
    numerical values that correspond to a quantity that has units.
    """

    unit_name: str | None = None
    """Term name that is associated with the CURIE of the units of the value or list of values in the 'value' property.

    The Units of Measurement Ontology (UO) SHOULD be used
    if possible. This property SHOULD be provided if a unit_id is
    provided. This is redundant but recommended for human readability.
    """

    @override
    def hash(self) -> str:
        # Skip more expensive default hash traversal
        # (No TOMBaseObject in FastJsonValue)
        return tomhash(
            (
                self.id,
                self.name,
                self.negated,
                self.operator,
                self.value,
                self.unit_id,
                self.unit_name,
            )
        )

    def met_by(self, attribute: Attribute | MetaAttribute) -> bool:
        """Check if the given attribute satisfies the constraint."""
        if isinstance(attribute, MetaAttribute):
            return (
                self.id == attribute.attribute_type_id
                and attribute.constraint_use is not False
            )

        if self.id != attribute.attribute_type_id:
            return False

        if self.operator == "===":
            result = attribute.value == self.value
        else:
            attr_vals = (
                attribute.value
                if isinstance(attribute.value, list)
                else [attribute.value]
            )
            con_vals = self.value if isinstance(self.value, list) else [self.value]

            match self.operator:
                case "==":
                    result = any(av == cv for av in attr_vals for cv in con_vals)
                case ">" | "<":
                    result = any(
                        (av > cv if self.operator == ">" else av < cv)
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

        return not result if self.negated else result
