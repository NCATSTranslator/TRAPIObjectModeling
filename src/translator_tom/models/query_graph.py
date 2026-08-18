from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from pydantic import Field
from typing_extensions import Self

from translator_tom.models.attribute import AttributeConstraint
from translator_tom.models.constraints import QEdgeConstraints
from translator_tom.models.path_constraint import PathConstraint
from translator_tom.models.shared import (
    CURIE,
    KnowledgeType,
    QEdgeID,
    QNodeID,
    QPathID,
)
from translator_tom.utils.biolink import Biolink
from translator_tom.utils.object_base import TOMBase

__all__ = [
    "QEdge",
    "QNode",
    "QPath",
    "QueryGraph",
    "SetInterpretation",
    "SetInterpretationEnum",
]


class QueryGraph(TOMBase):
    """A graph representing a biomedical question.

    It serves as a template for each Result (answer), where each bound
    knowledge graph node/edge is expected to obey the constraints of the
    associated QueryGraph element.
    """

    nodes: Annotated[dict[QNodeID, QNode], Field(min_length=1)]
    """The node specifications.

    The keys of this map are unique node
    identifiers and the corresponding values include the constraints
    on bound nodes.
    """

    edges: Annotated[dict[QEdgeID, QEdge], Field(min_length=1)] | None = None
    """The edge specifications.

    The keys of this map are unique edge
    identifiers and the corresponding values include the constraints
    on bound edges, in addition to specifying the subject and object QNodes.
    """

    paths: Annotated[dict[QPathID, QPath], Field(min_length=1, max_length=1)] | None = (
        None
    )
    """The QueryGraph path specification, used only for pathfinder type queries.

    The keys of this map are unique path identifiers and the
    corresponding values include the constraints on bound paths, in
    addition to specifying the subject, object, and intermediate QNodes.
    """

    @property
    def edges_dict(self) -> dict[QEdgeID, QEdge]:
        """Get the edges as a guaranteed dict, even if they are represented as None."""
        return self.edges if self.edges is not None else {}

    @property
    def paths_dict(self) -> dict[QPathID, QPath]:
        """Get the paths as a guaranteed dict, even if they are represented as None."""
        return self.paths if self.paths is not None else {}

    @classmethod
    def new(cls) -> Self:
        """Return an empty instance, without having to pass required containers."""
        return cls.model_construct(nodes={})


class SetInterpretationEnum(str, Enum):
    """Indicates how multiple CURIEs in the ids property MUST be interpreted."""

    BATCH = "BATCH"
    """BATCH indicates that the query is intended to be a batch query and each CURIE is treated independently."""

    MANY = "MANY"
    """MANY means that member CURIEs MUST form one or more sets in the Results, and sets with more members are generally considered more desirable that sets with fewer members."""

    ALL = "ALL"
    """ALL means that all specified CURIES MUST appear in each Result."""

    COLLATE = "COLLATE"
    """COLLATE indicates that multiple matching nodes MUST be collated into a single Result, rather than separated into separate Results."""


SetInterpretation = Literal["BATCH", "MANY", "ALL", "COLLATE"]


class QNode(TOMBase):
    """A node in the QueryGraph used to represent an entity in a query.

    If no CURIEs are not specified, any nodes matching the category
    of the QNode will be returned in the Results.
    """

    ids: Annotated[list[CURIE] | None, Field(min_length=1)] = None
    """A list of one or more CURIE identifiers for this node.

    The 'ids' property will hold a list of CURIEs only in the case of a
    BATCH set_interpretation, where each CURIE is queried
    separately. If a list of queried CURIEs is to be considered as a
    set (as under a MANY or ALL set_interpretation), the 'ids' property
    will hold a single id representing this set, and the individual members
    of this set will be captured in a separate 'member_ids' property.
    Note that the set id MUST be created as a UUID by the system that
    defines the queried set, using a centralized nodenorm service.
    Note also that downstream systems MUST re-use the original set UUID
    in the messages that they create/send to facilitate merging or
    caching operations.
    """

    categories: Annotated[list[Biolink.Entity] | None, Field(min_length=1)] = None
    """Biolink Model categories, which are allowed to be of type 'abstract' or 'mixin' (only in QGraphs!).

    Use of deprecated categories SHOULD be avoided.
    """

    set_interpretation: SetInterpretation | None = None
    """Indicates how multiple CURIEs in the ids property MUST be interpreted.

    BATCH indicates that the query is intended to be
    a batch query and each CURIE is treated independently. ALL means
    that all specified CURIES MUST appear in each Result.
    MANY means that member CURIEs MUST form one or more
    sets in the Results, and sets with more members are generally
    considered more desirable that sets with fewer members.
    Only when there are no ids provided, set_interpretation MAY be
    set to COLLATE to indicate that multiple matching nodes MUST be
    collated into a single Result, rather than separated into
    separate Results. If this property is absent, the default is
    BATCH.
    """

    member_ids: Annotated[list[CURIE] | None, Field(min_length=1)] = None
    """A list of CURIE identifiers for members of a queried set.

    This property MUST be populated under a set_interpretation of MANY
    or ALL, when the 'ids' property holds a UUID representing the set
    itself. This property MUST NOT be used under a set_interpretation
    of BATCH or COLLATE or when set_interpretation is absent.
    """

    constraints: Annotated[list[AttributeConstraint] | None, Field(min_length=1)] = None
    """A list of constraints applied to a query node.

    If there are multiple items, they must all be true (equivalent to AND).
    """

    @property
    def ids_list(self) -> list[CURIE]:
        """Get the IDs as a guaranteed list, even if they are represented as None."""
        return self.ids if self.ids is not None else []

    @property
    def categories_list(self) -> list[Biolink.Entity]:
        """Get the categories as a guaranteed list, even if they are represented as None."""
        return self.categories if self.categories is not None else []

    @property
    def member_ids_list(self) -> list[CURIE]:
        """Get the member_ids as a guaranteed list, even if they are represented as None."""
        return self.member_ids if self.member_ids is not None else []

    @property
    def constraints_list(self) -> list[AttributeConstraint]:
        """Get the attribute constraints as a guaranteed list, even if they are represented as None."""
        return self.constraints if self.constraints is not None else []


class QEdge(TOMBase):
    """An edge in the QueryGraph used as a filter pattern specification in a query.

    If the optional predicate property is not specified,
    it is assumed to be a wildcard match to the target knowledge space.
    If specified, the ontological inheritance hierarchy associated with
    the term provided is assumed, such that edge bindings returned may be
    an exact match to the given QEdge predicate term,
    or to a term that is a descendant of the QEdge predicate term.
    """

    knowledge_type: KnowledgeType | None = None
    """Indicates the type of knowledge that the client wants from the server between the subject and object.

    If the value is 'lookup', then the client wants direct lookup information from
    knowledge sources. If the value is 'inferred', then the client
    wants the server to get creative and connect the subject and
    object in more speculative and non-direct-lookup ways. If this
    property is absent, it MUST be assumed to mean 'lookup'.
    """

    predicates: Annotated[list[Biolink.Predicate] | None, Field(min_length=1)] = None
    """These should be Biolink Model predicates and are allowed to be of type 'abstract' or 'mixin' (only in QGraphs!).

    Use of 'deprecated' predicates SHOULD be avoided.
    """

    subject: QNodeID
    """Corresponds to the map key identifier of the subject concept node anchoring the query filter pattern for the query relationship edge."""

    object: QNodeID
    """Corresponds to the map key identifier of the object concept node anchoring the query filter pattern for the query relationship edge."""

    constraints: QEdgeConstraints | None = None
    """An object containing all constraints placed on the QEdge.

    ALL edges bound to this QEdge MUST conform to ALL given constraints;
    underlying edges (such as those appearing in supporting graphs)
    are not required to conform to the given constraints.
    """

    @property
    def predicates_list(self) -> list[Biolink.Predicate]:
        """Get the predicates as a guaranteed list, even if they are represented as None."""
        return self.predicates if self.predicates is not None else []

    def get_inverse(self) -> QEdge:
        """Get an inverse copy of the QEdge."""
        inverse_predicates = list[Biolink.Predicate]()
        failed_predicates = list[Biolink.Predicate]()
        for predicate in self.predicates_list:
            inverse = Biolink.get_inverse(predicate)
            if inverse is None:
                failed_predicates.append(predicate)
                continue
            inverse_predicates.append(inverse)

        if len(failed_predicates) > 0:
            raise ValueError(f"Cannot invert predicates {failed_predicates}.")

        return QEdge(
            knowledge_type=self.knowledge_type,
            predicates=inverse_predicates or None,
            subject=self.object,
            object=self.subject,
            constraints=(
                self.constraints.get_inverse() if self.constraints is not None else None
            ),
        )


class QPath(TOMBase):
    """A path in the QueryGraph used for pathfinder queries.

    Both subject and object MUST reference QNodes that have a CURIE in their ids property.
    Paths returned that bind to this QPath MUST represent some
    relationship between the subject and object.
    """

    subject: QNodeID
    """Corresponds to the map key identifier of the subject concept node for the start of the queried path."""

    object: QNodeID
    """Corresponds to the map key identifier of the object concept node for the end of the queried path."""

    predicates: Annotated[list[Biolink.Predicate] | None, Field(min_length=1)] = None
    """QPath predicates are intended to convey what type of paths are desired, NOT a constraint on the types of predicates that may be in result paths.

    If no predicate is listed, the ARA SHOULD find paths such that the
    relationship represented by the path is a "related_to" relationship.
    These should be Biolink Model predicates and are allowed to be of type
    'abstract' or 'mixin'. Use of 'deprecated' predicates SHOULD be avoided.
    """

    constraints: Annotated[list[PathConstraint] | None, Field(min_length=1)] = None
    """A list of constraints for the QPath.

    If multiple constraints are listed, it should be interpreted as an OR
    relationship. Each path returned MUST comply with at least one constraint.
    """

    @property
    def predicates_list(self) -> list[Biolink.Predicate]:
        """Get the predicates as a guaranteed list, even if they are represented as None."""
        return self.predicates if self.predicates is not None else []

    @property
    def constraints_list(self) -> list[PathConstraint]:
        """Get the constraints as a guaranteed list, even if they are represented as None."""
        return self.constraints if self.constraints is not None else []


# Don't defer model builds
QueryGraph.model_rebuild()
