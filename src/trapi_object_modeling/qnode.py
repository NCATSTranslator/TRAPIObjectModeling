from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from trapi_object_modeling.attribute_constraint import AttributeConstraint
from trapi_object_modeling.shared import CURIE, BiolinkEntity


class SetInterpetationEnum(str, Enum):
    """Indicates how multiple CURIEs in the ids property MUST be interpreted."""

    BATCH = "BATCH"
    """BATCH indicates that the query is intended to be a batch query and each CURIE is treated independently."""

    MANY = "MANY"
    """ALL means that all specified CURIES MUST appear in each Result."""

    ALL = "ALL"
    """MANY means that member CURIEs MUST form one or more sets in the Results, and sets with more members are generally considered more desirable that sets with fewer members."""


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
class QNode:
    """A node in the QueryGraph used to represent an entity in a query.

    If a CURIE is not specified, any nodes matching the category
    of the QNode will be returned in the Results.
    """

    ids: Annotated[list[CURIE] | None, Field(min_length=1)] = None
    """A CURIE identifier (or list of identifiers) for this node.

    The 'ids' field will hold a list of CURIEs only in the case of a
    BATCH set_interpretation, where each CURIE is queried
    separately. If a list of queried CURIEs is to be considered as a
    set (as under a MANY or ALL set_interpretation), the 'ids' field
    will hold a single id representing this set, and the individual members
    of this set will be captured in a separate 'member_ids' field.
    Note that the set id MUST be created as a UUID by the system that
    defines the queried set, using a centralized nodenorm service.
    Note also that downstream systems MUST re-use the original set UUID
    in the messages they create/send, which will facilitate merging or
    caching operations.
    """

    categories: Annotated[list[BiolinkEntity] | None, Field(min_length=1)] = None
    """These should be Biolink Model categories and are allowed to be of type 'abstract' or 'mixin' (only in QGraphs!).

    Use of 'deprecated' categories should be avoided.
    """

    set_interpretation: SetInterpetationEnum | None = None
    """Indicates how multiple CURIEs in the ids property MUST be interpreted.

    BATCH indicates that the query is intended to be
    a batch query and each CURIE is treated independently. ALL means
    that all specified CURIES MUST appear in each Result.
    MANY means that member CURIEs MUST form one or more
    sets in the Results, and sets with more members are generally
    considered more desirable that sets with fewer members.
    If this property is missing or null, the default is BATCH.
    """

    member_ids: list[CURIE] | None = None
    """A list of CURIE identifiers for members of a queried set.

    This field MUST be populated under a set_interpretation of MANY
    or ALL, when the 'ids' field holds a UUID representing the set
    itself. This field MUST NOT be used under a set_interpretation
    of BATCH."""

    constraints: list[AttributeConstraint] | None = None
    """A list of constraints applied to a query node.

    If there are multiple items, they must all be true (equivalent to AND).
    """
