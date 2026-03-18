from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, override

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from trapi_object_modeling.attribute_constraint import AttributeConstraint
from trapi_object_modeling.path_constraint import PathConstraint
from trapi_object_modeling.qualifier_constraint import QualifierConstraint
from trapi_object_modeling.shared import (
    CURIE,
    BiolinkEntity,
    BiolinkPredicate,
    KnowledgeTypeEnum,
    QEdgeID,
    QNodeID,
    QPathID,
)
from trapi_object_modeling.utils.object_base import (
    Location,
    SemanticValidationError,
    SemanticValidationErrorList,
    SemanticValidationResult,
    SemanticValidationWarningList,
    TOMBaseObject,
)
from trapi_object_modeling.utils.semantic_validation import (
    always_valid,
    extend_location,
    get_dict_locations,
    get_list_locations,
    validate_category,
    validate_many,
    validate_node_exists,
    validate_predicate,
    validation_pipeline,
)


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
class BaseQueryGraph(TOMBaseObject):
    """A graph representing a biomedical question.

    It serves as a template for
    each result (answer), where each bound knowledge graph node/edge is
    expected to obey the constraints of the associated query graph element.
    """

    nodes: dict[QNodeID, QNode]
    """The node specifications.

    The keys of this map are unique node
    identifiers and the corresponding values include the constraints
    on bound nodes.
    """

    def validate_qnodes_exist(
        self, qnodes: list[QNodeID], location: Location | None = None
    ) -> SemanticValidationResult:
        """Check that every given QNodeID is present in the nodes."""
        warnings, errors = (
            SemanticValidationWarningList(),
            SemanticValidationErrorList(),
        )
        for qnode_id in qnodes:
            if qnode_id not in self.nodes:
                errors.append(
                    SemanticValidationError(
                        f"QNode {qnode_id} is not present in query_graph.",
                        location or (),
                    )
                )

        return warnings, errors

    @override
    def semantic_validate(
        self, location: Location | None = None, **kwargs: Any
    ) -> SemanticValidationResult:
        return validate_many(
            *self.nodes.values(),
            location=get_dict_locations(self.nodes, extend_location(location, "nodes")),
        )


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
class QueryGraph(BaseQueryGraph):
    """A non-Pathfinder query SHOULD have edges following the QEdge schema and SHOULD NOT have paths."""

    edges: dict[QEdgeID, QEdge]
    """The edge specifications.

    The keys of this map are unique edge
    identifiers and the corresponding values include the constraints
    on bound edges, in addition to specifying the subject and object QNodes.
    """

    def validate_qedges_exist(
        self, qedges: list[QEdgeID], location: Location | None = None
    ) -> SemanticValidationResult:
        """Check that every given QEdgeID is present in the edges."""
        warnings, errors = (
            SemanticValidationWarningList(),
            SemanticValidationErrorList(),
        )
        for qedge_id in qedges:
            if qedge_id not in self.edges:
                errors.append(
                    SemanticValidationError(
                        f"QEdge {qedge_id} is not present in query_graph.",
                        location or (),
                    )
                )

        return warnings, errors

    @override
    def semantic_validate(
        self, location: Location | None = None, **kwargs: Any
    ) -> SemanticValidationResult:
        return validation_pipeline(
            super().semantic_validate(location, **kwargs),
            validate_many(
                *self.edges.values(),
                locations=get_dict_locations(
                    self.edges, extend_location(location, "edges")
                ),
                qgraph=self,
            ),
        )


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
class PathfinderQueryGraph(BaseQueryGraph):
    """A Pathfinder query SHOULD have paths following the QPath schema and SHOULD NOT have edges."""

    paths: Annotated[dict[QPathID, QPath], Field(min_length=1, max_length=1)]
    """The QueryGraph path specification, used only for pathfinder type queries.

    The keys of this map are unique path identifiers and the
    corresponding values include the constraints on bound paths, in
    addition to specifying the subject, object, and intermediate QNodes.
    """

    def validate_paths_exist(
        self, qpaths: list[QPathID], location: Location | None = None
    ) -> SemanticValidationResult:
        """Check that every given QPathID is present in the paths."""
        warnings, errors = (
            SemanticValidationWarningList(),
            SemanticValidationErrorList(),
        )
        for qpath_id in qpaths:
            if qpath_id not in self.paths:
                errors.append(
                    SemanticValidationError(
                        f"QPath {qpath_id} is not present in query_graph.",
                        location or (),
                    )
                )

        return warnings, errors

    @override
    def semantic_validate(
        self, location: Location | None = None, **kwargs: Any
    ) -> SemanticValidationResult:
        return validation_pipeline(
            super().semantic_validate(location, **kwargs),
            validate_many(
                *self.paths.values(),
                locations=get_dict_locations(
                    self.paths, extend_location(location, "paths")
                ),
                qgraph=self,
            ),
        )


class SetInterpetationEnum(str, Enum):
    """Indicates how multiple CURIEs in the ids property MUST be interpreted."""

    BATCH = "BATCH"
    """BATCH indicates that the query is intended to be a batch query and each CURIE is treated independently."""

    MANY = "MANY"
    """ALL means that all specified CURIES MUST appear in each Result."""

    ALL = "ALL"
    """MANY means that member CURIEs MUST form one or more sets in the Results, and sets with more members are generally considered more desirable that sets with fewer members."""


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
class QNode(TOMBaseObject):
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

    @property
    def categories_list(self) -> list[BiolinkEntity]:
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

    @override
    def semantic_validate(
        self, location: Location | None = None, **kwargs: Any
    ) -> SemanticValidationResult:
        return validation_pipeline(
            *(
                validate_category(cat, extend_location(location, "categories"))
                for cat in self.categories_list
            ),
            validate_many(
                *self.constraints_list,
                locations=get_list_locations(
                    self.constraints_list, extend_location(location, "constraints")
                ),
            ),
        )


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
class QEdge(TOMBaseObject):
    """An edge in the QueryGraph used as a filter pattern specification in a query.

    If the optional predicate property is not specified,
    it is assumed to be a wildcard match to the target knowledge space.
    If specified, the ontological inheritance hierarchy associated with
    the term provided is assumed, such that edge bindings returned may be
    an exact match to the given QEdge predicate term,
    or to a term that is a descendant of the QEdge predicate term.
    """

    knowledge_type: KnowledgeTypeEnum | None = None
    """Indicates the type of knowledge that the client wants from the server between the subject and object.

    If the value is 'lookup', then the client wants direct lookup information from
    knowledge sources. If the value is 'inferred', then the client
    wants the server to get creative and connect the subject and
    object in more speculative and non-direct-lookup ways. If this
    property is absent or null, it MUST be assumed to mean
    'lookup'. This feature is currently experimental and may be
    further extended in the future.
    """

    predicates: Annotated[list[BiolinkPredicate] | None, Field(min_length=1)] = None
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
    def predicates_list(self) -> list[BiolinkPredicate]:
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

    @override
    def semantic_validate(
        self,
        location: Location | None = None,
        qgraph: QueryGraph | None = None,
        **kwargs: Any,
    ) -> SemanticValidationResult:
        warnings, errors = validation_pipeline(
            (
                validate_node_exists(
                    self,
                    "subject",
                    qgraph,
                    "query_graph",
                    extend_location(location, "subject"),
                )
                if qgraph is not None
                else always_valid()
            ),
            (
                validate_node_exists(
                    self,
                    "object",
                    qgraph,
                    "query_graph",
                    extend_location(location, "object"),
                )
                if qgraph is not None
                else always_valid()
            ),
            *(
                validate_predicate(predicate, extend_location(location, "predicates"))
                for predicate in self.predicates_list
            ),
            validate_many(
                *self.qualifier_constraints_list,
                locations=get_list_locations(
                    self.qualifier_constraints_list,
                    extend_location(location, "qualifier_constraints"),
                ),
            ),
            validate_many(
                *self.attribute_constraints_list,
                locations=get_list_locations(
                    self.attribute_constraints_list,
                    extend_location(location, "attribute_constraints"),
                ),
            ),
        )

        if qgraph is None:
            return warnings, errors

        if self.subject not in qgraph.edges:
            errors.append(
                SemanticValidationError(
                    f"Subject `{self.subject}` is not present in query_graph.",
                    extend_location(location, "subject"),
                )
            )
        if self.object not in qgraph.edges:
            errors.append(
                SemanticValidationError(
                    f"Object `{self.object}` is not present in query_graph.",
                    extend_location(location, "object"),
                )
            )

        return warnings, errors


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
class QPath(TOMBaseObject):
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

    @property
    def predicates_list(self) -> list[BiolinkPredicate]:
        """Get the predicates as a guaranteed list, even if they are represented as None."""
        return self.predicates if self.predicates is not None else []

    @property
    def constraints_list(self) -> list[PathConstraint]:
        """Get the constraints as a guaranteed list, even if they are represented as None."""
        return self.constraints if self.constraints is not None else []

    @override
    def semantic_validate(
        self,
        location: Location | None = None,
        qgraph: QueryGraph | None = None,
        **kwargs: Any,
    ) -> SemanticValidationResult:
        return validation_pipeline(
            (
                validate_node_exists(
                    self,
                    "subject",
                    qgraph,
                    "query_graph",
                    extend_location(location, "subject"),
                )
                if qgraph is not None
                else always_valid()
            ),
            (
                validate_node_exists(
                    self,
                    "object",
                    qgraph,
                    "query_graph",
                    extend_location(location, "object"),
                )
                if qgraph is not None
                else always_valid()
            ),
            *(
                validate_predicate(predicate, extend_location(location, "predicates"))
                for predicate in self.predicates_list
            ),
            validate_many(
                *self.constraints_list,
                locations=get_list_locations(
                    self.constraints_list, extend_location(location, "constraints")
                ),
            ),
        )
