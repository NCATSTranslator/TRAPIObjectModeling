from __future__ import annotations

from typing import Annotated

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from trapi_object_modeling.path_constraint import PathConstraint
from trapi_object_modeling.shared import (
    BiolinkPredicate,
    QNodeID,
)


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
class QPath:
    """A path in the QueryGraph used for pathfinder queries.

    Both subject and object MUST reference QNodes that have a CURIE in their ids field.
    Paths returned that bind to this QPath can represent some
    relationship between subject and object.
    """

    subject: QNodeID
    """Corresponds to the map key identifier of the subject concept node for the start of the queried path."""

    object: QNodeID
    """Corresponds to the map key identifier of the object concept node for the end of the queried path."""

    predicates: Annotated[list[BiolinkPredicate] | None, Field(min_length=1)] = None
    """QPath predicates are intended to convey what type of paths are desired, NOT a constraint on the types of predicates that may be in result paths.

    If no predicate is listed, the ARA SHOULD find paths such that the
    relationship represented by the path is a "related_to" relationship.
    These should be Biolink Model predicates and are allowed to be of type
    'abstract' or 'mixin' (only in QGraphs!). Use of 'deprecated'
    predicates should be avoided.
    """

    constraints: Annotated[list[PathConstraint] | None, Field(min_length=1)] = None
    """A list of constraints for the QPath.

    If multiple constraints are listed, it should be interpreted as an OR relationship. Each path returned is
    required to comply with at least one constraint.
    """
