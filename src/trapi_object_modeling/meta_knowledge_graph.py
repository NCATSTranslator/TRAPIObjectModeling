from __future__ import annotations

from typing import Annotated, Any, override

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from trapi_object_modeling.meta_attribute import MetaAttribute
from trapi_object_modeling.meta_qualifier import MetaQualifier
from trapi_object_modeling.shared import (
    BiolinkEntity,
    BiolinkPredicate,
    KnowledgeTypeEnum,
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
    validate_association,
    validate_category,
    validate_many,
    validate_predicate,
    validation_pipeline,
)


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
class MetaKnowledgeGraph(TOMBaseObject):
    """Knowledge-map representation of this TRAPI web service.

    The meta knowledge graph is composed of the union of most specific categories
    and predicates for each node and edge.
    """

    nodes: dict[BiolinkEntity, MetaNode]
    """Collection of the most specific node categories provided by this TRAPI web service, indexed by Biolink class CURIEs.

    A node category is only exposed here if there is
    node for which that is the most specific category available.
    """

    edges: list[MetaEdge]
    """List of the most specific edges/predicates provided by this TRAPI web service.

    A predicate is only exposed here if there is an edge
    for which the predicate is the most specific available.
    """

    @override
    def semantic_validate(
        self, location: Location | None = None, **kwargs: Any
    ) -> SemanticValidationResult:
        return validation_pipeline(
            *(
                validate_category(cat, extend_location(location, "nodes"))
                for cat in self.nodes
            ),
            validate_many(
                *self.nodes.values(),
                locations=get_dict_locations(
                    self.nodes, extend_location(location, "nodes")
                ),
            ),
            validate_many(
                *self.edges,
                locations=get_list_locations(
                    self.edges, extend_location(location, "edges")
                ),
                metakg=self,
            ),
        )

    def validate_nodes_exist(
        self, nodes: list[BiolinkEntity], location: Location | None = None
    ) -> SemanticValidationResult:
        """Check that every given CURIE is present in the nodes."""
        warnings, errors = (
            SemanticValidationWarningList(),
            SemanticValidationErrorList(),
        )
        for category in nodes:
            if category not in self.nodes:
                errors.append(
                    SemanticValidationError(
                        f"Node {category} is not present in meta_knowledge_graph.",
                        location or (),
                    )
                )

        return warnings, errors


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class MetaNode(TOMBaseObject):
    """Description of a node category provided by this TRAPI web service."""

    id_prefixes: Annotated[list[str], Field(min_length=1)]
    """List of CURIE prefixes for the node category that this TRAPI web service understands and accepts on the input."""

    attributes: list[MetaAttribute] | None = None
    """Node attributes provided by this TRAPI web service."""

    @property
    def attributes_list(self) -> list[MetaAttribute]:
        """Get the meta attributes as a guaranteed list, even if they are represented as None."""
        return self.attributes if self.attributes is not None else []

    @override
    def semantic_validate(
        self, location: Location | None = None, **kwargs: Any
    ) -> SemanticValidationResult:
        return validate_many(
            *self.attributes_list,
            locations=get_list_locations(
                self.attributes_list, extend_location(location, "attributes")
            ),
        )


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class MetaEdge(TOMBaseObject):
    """Edge in a meta knowledge map describing relationship between a subject Biolink class and an object Biolink class."""

    subject: BiolinkEntity
    """Subject node category of this relationship edge."""

    predicate: BiolinkPredicate
    """Biolink relationship between the subject and object categories."""

    object: BiolinkEntity
    """Object node category of this relationship edge."""

    knowledge_types: Annotated[list[KnowledgeTypeEnum] | None, Field(min_length=1)] = (
        None
    )
    """A list of knowledge_types that are supported by the service.

    If the knowledge_types is null, this means that only 'lookup'
    is supported. Currently allowed values are 'lookup' or 'inferred'.
    """

    attributes: list[MetaAttribute] | None = None
    """Edge attributes provided by this TRAPI web service."""

    qualifiers: list[MetaQualifier] | None = None
    """Qualifiers that are possible to be found on this edge type."""

    association: BiolinkEntity | None = None
    """The Biolink association type (entity) that this edge represents.

    Associations are classes in Biolink
    that represent a relationship between two entities.
    For example, the association 'gene interacts with gene'
    is represented by the Biolink class,
    'biolink:GeneToGeneAssociation'.  If association
    is filled out, then the testing harness can
    help validate that the qualifiers are being used
    correctly.
    """

    @property
    def attributes_list(self) -> list[MetaAttribute]:
        """Get the meta attributes as a guaranteed list, even if they are represented as None."""
        return self.attributes if self.attributes is not None else []

    @property
    def qualifiers_list(self) -> list[MetaQualifier]:
        """Get the meta qualifiers as a guaranteed list, even if they are represented as None."""
        return self.qualifiers if self.qualifiers is not None else []

    @override
    def semantic_validate(
        self,
        location: Location | None = None,
        metakg: MetaKnowledgeGraph | None = None,
        **kwargs: Any,
    ) -> SemanticValidationResult:
        return validation_pipeline(
            validate_category(self.subject, extend_location(location, "subject")),
            (
                metakg.validate_nodes_exist(
                    [self.subject], extend_location(location, "subject")
                )
                if metakg is not None
                else always_valid()
            ),
            (
                metakg.validate_nodes_exist(
                    [self.object], extend_location(location, "object")
                )
                if metakg is not None
                else always_valid()
            ),
            validate_category(self.object, extend_location(location, "object")),
            validate_predicate(self.predicate, extend_location(location, "predicate")),
            validate_many(
                *self.attributes_list,
                locations=get_list_locations(
                    self.attributes_list, extend_location(location, "attributes")
                ),
            ),
            validate_many(
                *self.qualifiers_list,
                locations=get_list_locations(
                    self.qualifiers_list, extend_location(location, "qualifiers")
                ),
            ),
            validate_association(
                self.association, extend_location(location, "association")
            )
            if self.association is not None
            else always_valid(),
        )
