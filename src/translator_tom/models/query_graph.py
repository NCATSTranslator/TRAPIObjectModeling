from __future__ import annotations

from enum import Enum
from typing import Annotated, ClassVar, Literal

from pydantic import ConfigDict, Field

from translator_tom.models.attribute import AttributeConstraint
from translator_tom.models.path_constraint import PathConstraint
from translator_tom.models.qualifier import QualifierConstraint
from translator_tom.models.shared import (
    CURIE,
    KnowledgeType,
    QEdgeID,
    QNodeID,
    QPathID,
)
from translator_tom.utils.biolink import Biolink
from translator_tom.utils.object_base import TOMBaseObject


class BaseQueryGraph(TOMBaseObject):
    """A graph representing a biomedical question.

    It serves as a template for
    each result (answer), where each bound knowledge graph node/edge is
    expected to obey the constraints of the associated query graph element.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")

    nodes: dict[QNodeID, QNode]
    """The node specifications.

    The keys of this map are unique node
    identifiers and the corresponding values include the constraints
    on bound nodes.
    """


class QueryGraph(BaseQueryGraph):
    """A non-Pathfinder query SHOULD have edges following the QEdge schema and SHOULD NOT have paths."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")

    edges: dict[QEdgeID, QEdge]
    """The edge specifications.

    The keys of this map are unique edge
    identifiers and the corresponding values include the constraints
    on bound edges, in addition to specifying the subject and object QNodes.
    """


class PathfinderQueryGraph(BaseQueryGraph):
    """A Pathfinder query SHOULD have paths following the QPath schema and SHOULD NOT have edges."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")

    paths: Annotated[dict[QPathID, QPath], Field(min_length=1, max_length=1)]
    """The QueryGraph path specification, used only for pathfinder type queries.

    The keys of this map are unique path identifiers and the
    corresponding values include the constraints on bound paths, in
    addition to specifying the subject, object, and intermediate QNodes.
    """


class SetInterpretationEnum(str, Enum):
    """Indicates how multiple CURIEs in the ids property MUST be interpreted."""

    BATCH = "BATCH"
    """BATCH indicates that the query is intended to be a batch query and each CURIE is treated independently."""

    MANY = "MANY"
    """MANY means that member CURIEs MUST form one or more sets in the Results, and sets with more members are generally considered more desirable that sets with fewer members."""

    ALL = "ALL"
    """ALL means that all specified CURIES MUST appear in each Result."""


SetInterpretation = Literal["BATCH", "MANY", "ALL"]


class QNode(TOMBaseObject):
    """A node in the QueryGraph used to represent an entity in a query.

    If a CURIE is not specified, any nodes matching the category
    of the QNode will be returned in the Results.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")

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

    categories: Annotated[list[Biolink.Entity] | None, Field(min_length=1)] = None
    """These should be Biolink Model categories and are allowed to be of type 'abstract' or 'mixin' (only in QGraphs!).

    Use of 'deprecated' categories should be avoided.
    """

    set_interpretation: SetInterpretation | None = None
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


class QEdge(TOMBaseObject):
    """An edge in the QueryGraph used as a filter pattern specification in a query.

    If the optional predicate property is not specified,
    it is assumed to be a wildcard match to the target knowledge space.
    If specified, the ontological inheritance hierarchy associated with
    the term provided is assumed, such that edge bindings returned may be
    an exact match to the given QEdge predicate term,
    or to a term that is a descendant of the QEdge predicate term.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")

    knowledge_type: KnowledgeType | None = None
    """Indicates the type of knowledge that the client wants from the server between the subject and object.

    If the value is 'lookup', then the client wants direct lookup information from
    knowledge sources. If the value is 'inferred', then the client
    wants the server to get creative and connect the subject and
    object in more speculative and non-direct-lookup ways. If this
    property is absent or null, it MUST be assumed to mean
    'lookup'. This feature is currently experimental and may be
    further extended in the future.
    """

    predicates: Annotated[list[Biolink.Predicate] | None, Field(min_length=1)] = None
    """These should be Biolink Model predicates and are allowed to be of type 'abstract' or 'mixin' (only in QGraphs!).

    Use of 'deprecated' predicates should be avoided."""

    subject: QNodeID
    """Corresponds to the map key identifier of the subject concept node anchoring the query filter pattern for the query relationship edge."""

    object: QNodeID
    """Corresponds to the map key identifier of the object concept node anchoring the query filter pattern for the query relationship edge."""

    attribute_constraints: list[AttributeConstraint] | None = None
    """A list of attribute constraints applied to a query edge. If there are multiple items, they must all be true (equivalent to AND)."""

    qualifier_constraints: list[QualifierConstraint] | None = None
    """A list of QualifierConstraints that provide nuance to the QEdge.

    If multiple QualifierConstraints are provided, there is an OR
    relationship between them. If the QEdge has multiple
    predicates or if the QNodes that correspond to the subject or
    object of this QEdge have multiple categories or multiple
    curies, then qualifier_constraints MUST NOT be specified
    because these complex use cases are not supported at this time.
    """

    @property
    def predicates_list(self) -> list[Biolink.Predicate]:
        """Get the predicates as a guaranteed list, even if they are represented as None."""
        return self.predicates if self.predicates is not None else []

    @property
    def attribute_constraints_list(self) -> list[AttributeConstraint]:
        """Get the attribute_constraints as a guaranteed list, even if they are represented as None."""
        return (
            self.attribute_constraints if self.attribute_constraints is not None else []
        )

    @property
    def qualifier_constraints_list(self) -> list[QualifierConstraint]:
        """Get the qualifier_constraints as a guaranteed list, even if they are represented as None."""
        return (
            self.qualifier_constraints if self.qualifier_constraints is not None else []
        )


class QPath(TOMBaseObject):
    """A path in the QueryGraph used for pathfinder queries.

    Both subject and object MUST reference QNodes that have a CURIE in their ids field.
    Paths returned that bind to this QPath can represent some
    relationship between subject and object.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")

    subject: QNodeID
    """Corresponds to the map key identifier of the subject concept node for the start of the queried path."""

    object: QNodeID
    """Corresponds to the map key identifier of the object concept node for the end of the queried path."""

    predicates: Annotated[list[Biolink.Predicate] | None, Field(min_length=1)] = None
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

    @property
    def predicates_list(self) -> list[Biolink.Predicate]:
        """Get the predicates as a guaranteed list, even if they are represented as None."""
        return self.predicates if self.predicates is not None else []

    @property
    def constraints_list(self) -> list[PathConstraint]:
        """Get the constraints as a guaranteed list, even if they are represented as None."""
        return self.constraints if self.constraints is not None else []
