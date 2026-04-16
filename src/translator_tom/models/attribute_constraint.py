from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from pydantic import ConfigDict, Field, JsonValue, SkipValidation
from pydantic.dataclasses import dataclass

from translator_tom.models.shared import CURIE
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


@dataclass(
    kw_only=True,
    eq=True,
    unsafe_hash=True,
    config=ConfigDict(extra="ignore", serialize_by_alias=True),
)
class AttributeConstraint(TOMBaseObject):
    """Generic query constraint for a query node or query edge."""

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

    # JSON value inherently doesn't need validation if you're validating from JSON
    value: SkipValidation[JsonValue]
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
