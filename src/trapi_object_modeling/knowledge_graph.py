from __future__ import annotations

import itertools
from typing import Annotated, Any, Literal, override

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass
from stablehash import stablehash

from trapi_object_modeling.attribute import Attribute
from trapi_object_modeling.attribute_constraint import AttributeConstraint
from trapi_object_modeling.qualifier import Qualifier
from trapi_object_modeling.retrieval_source import ResourceRoleEnum, RetrievalSource
from trapi_object_modeling.shared import (
    CURIE,
    BiolinkEntity,
    BiolinkPredicate,
    EdgeID,
    Infores,
    biolink,
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
class KnowledgeGraph(TOMBaseObject):
    """The knowledge graph associated with a set of results.

    The instances of Node and Edge defining this graph represent instances of
    biolink:NamedThing (concept nodes) and biolink:Association
    (relationship edges) representing (Attribute) annotated knowledge
    returned from the knowledge sources and inference agents wrapped by
    the given TRAPI implementation.
    """

    nodes: dict[CURIE, Node]
    """Dictionary of Node instances used in the KnowledgeGraph, referenced elsewhere in the TRAPI output by the dictionary key."""

    edges: dict[EdgeID, Edge]
    """Dictionary of Edge instances used in the KnowledgeGraph, referenced elsewhere in the TRAPI output by the dictionary key."""

    def validate_edges_exist(
        self, edges: list[EdgeID], location: Location | None = None
    ) -> SemanticValidationResult:
        """Check that every given EdgeID is present in the edges."""
        warnings, errors = (
            SemanticValidationWarningList(),
            SemanticValidationErrorList(),
        )
        for edge_id in edges:
            if edge_id not in self.edges:
                errors.append(
                    SemanticValidationError(
                        f"Edge {edge_id} is not present in knowledge_graph.",
                        location or (),
                    )
                )

        return warnings, errors

    def validate_nodes_exist(
        self, nodes: list[CURIE], location: Location | None = None
    ) -> SemanticValidationResult:
        """Check that every given CURIE is present in the nodes."""
        warnings, errors = (
            SemanticValidationWarningList(),
            SemanticValidationErrorList(),
        )
        for node_id in nodes:
            if node_id not in self.nodes:
                errors.append(
                    SemanticValidationError(
                        f"Node {node_id} is not present in knowledge_graph.",
                        location or (),
                    )
                )

        return warnings, errors

    @override
    def semantic_validate(
        self, location: Location | None = None, **kwargs: Any
    ) -> SemanticValidationResult:
        return validation_pipeline(
            validate_many(
                *self.nodes.values(),
                locations=get_dict_locations(
                    self.nodes, extend_location(location, "nodes")
                ),
            ),
            validate_many(
                *self.edges.values(),
                locations=get_dict_locations(
                    self.edges, extend_location(location, "edges")
                ),
                kgraph=self,
            ),
        )

    def normalize(self) -> dict[EdgeID, EdgeID]:
        """Normalize the kgraph edge IDs and return a mapping of new:old."""
        mapping = dict[EdgeID, EdgeID]()

        for edge_id in list(self.edges.keys()):
            edge = self.edges.pop(edge_id)
            new_id = edge.hash()
            mapping[edge_id] = new_id
            self.edges[new_id] = edge

        return mapping

    def update(
        self,
        other: KnowledgeGraph,
        pre_normalized: Literal["neither", "both", "self", "other"] = "neither",
    ) -> dict[EdgeID, EdgeID]:
        """Update the kgraph in-place using the other.

        Returns a mapping of old:new EdgeIDs if normalization was done.
        """
        mapping = dict[EdgeID, EdgeID]()
        if pre_normalized in ("neither", "other"):
            mapping.update(self.normalize())
        if pre_normalized in ("neither", "self"):
            # Normalize a shallow copy of the other dict so as not to modify the original
            other = KnowledgeGraph(nodes=dict(other.nodes), edges=dict(other.edges))
            mapping.update(other.normalize())

        for node_id, node in other.nodes.items():
            if node_id in self.nodes:
                self.nodes[node_id].update(node)
                continue
            self.nodes[node_id] = node

        for edge_id, edge in other.edges.items():
            if edge_id in self.edges:
                self.edges[edge_id].update(edge)
                continue
            self.edges[edge_id] = edge

        return mapping


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class Node(TOMBaseObject):
    """A node in the KnowledgeGraph which represents some biomedical concept.

    Nodes are identified by the keys in the KnowledgeGraph Node mapping.
    """

    name: str | None = None
    """Formal name of the entity."""

    categories: Annotated[list[BiolinkEntity], Field(min_length=1)]
    """These should be Biolink Model categories and are NOT allowed to be of type 'abstract' or 'mixin'.

    Returning 'deprecated' categories should also be avoided.
    """

    attributes: list[Attribute]
    """A list of attributes describing the node."""

    is_set: bool | None = None
    """Indicates that the node represents a set of entities.

    If this property is missing or null, it is assumed to be false.
    """

    @override
    def hash(self) -> str:
        return stablehash((self.name, self.is_set)).hexdigest()

    @override
    def semantic_validate(
        self, location: Location | None = None, **kwargs: Any
    ) -> SemanticValidationResult:
        return validation_pipeline(
            *(
                validate_category(category, extend_location(location, "categories"))
                for category in self.categories
            ),
            validate_many(
                *self.attributes,
                location=get_list_locations(
                    self.attributes, extend_location(location, "attributes")
                ),
            ),
        )

    def meets_constraints(self, constraints: list[AttributeConstraint]) -> bool:
        """Check if all constraints are satisfied by the node's attributes."""
        attrs_by_type: dict[CURIE, list[Attribute]] = {}
        for attr in self.attributes:
            attrs_by_type.setdefault(attr.attribute_type_id, []).append(attr)
        return all(
            any(attr.meets_constraint(c) for attr in attrs_by_type.get(c.id, []))
            for c in constraints
        )

    def update(self, other: Node) -> None:
        """Update the node in-place with another node."""
        self.name = other.name or self.name
        if other.categories:
            self.categories = list(set(self.categories) | set(other.categories))
        if other.attributes:
            attrs = {attr.hash(): attr for attr in self.attributes}
            new_attrs = {attr.hash(): attr for attr in other.attributes}
            self.attributes = list({**attrs, **new_attrs}.values())


@dataclass(kw_only=True, config=ConfigDict(extra="ignore"))
class Edge(TOMBaseObject):
    """A specification of the semantic relationship linking two concepts that are expressed as nodes in the knowledge "thought" graph resulting from a query upon the underlying knowledge source."""

    predicate: BiolinkPredicate
    """The type of relationship between the subject and object for the statement expressed in an Edge.

    These should be Biolink Model predicate terms and are NOT allowed

    to be of type 'abstract' or 'mixin'. Returning 'deprecated'
    predicate terms should also be avoided."""

    subject: CURIE
    """Corresponds to the map key CURIE of the subject concept node of this relationship edge."""

    object: CURIE
    """Corresponds to the map key CURIE of the object concept node of this relationship edge."""

    attributes: list[Attribute] | None = None
    """A list of additional attributes for this edge."""

    qualifiers: list[Qualifier] | None = None
    """A set of Qualifiers that act together to add nuance or detail to the statement expressed in an Edge."""

    sources: Annotated[list[RetrievalSource], Field(min_length=1)]

    @property
    def attributes_list(self) -> list[Attribute]:
        """Get the attributes as a guaranteed list, even if they are represented as None."""
        return self.attributes if self.attributes is not None else []

    @property
    def qualifiers_list(self) -> list[Qualifier]:
        """Get the qualifiers as a guaranteed list, even if they are represented as None."""
        return self.qualifiers if self.qualifiers is not None else []

    @property
    def primary_knowledge_source(self) -> RetrievalSource:
        """The primary knowledge source of the edge."""
        for source in self.sources:
            if source.resource_role == ResourceRoleEnum.primary_knowledge_source:
                return source

        raise ValueError(
            f"Edge {self.subject} -{self.predicate}-> {self.object} has no primary_knowledge_source!"
        )

    @override
    def hash(self) -> str:
        return stablehash(
            (
                self.subject,
                self.object,
                self.predicate,
                self.qualifiers,
                self.primary_knowledge_source.resource_id,
            )
        ).hexdigest()

    @override
    def semantic_validate(
        self,
        location: Location | None = None,
        kgraph: KnowledgeGraph | None = None,
        **kwargs: Any,
    ) -> SemanticValidationResult:
        warnings, errors = validation_pipeline(
            (
                validate_node_exists(
                    self,
                    "subject",
                    kgraph,
                    "knowledge_graph",
                    extend_location(location, "subject"),
                )
                if kgraph is not None
                else always_valid()
            ),
            (
                validate_node_exists(
                    self,
                    "object",
                    kgraph,
                    "knowledge_graph",
                    extend_location(location, "object"),
                )
                if kgraph is not None
                else always_valid()
            ),
            validate_predicate(self.predicate, extend_location(location, "predicate")),
            validate_many(
                *self.qualifiers_list,
                locations=get_list_locations(
                    self.qualifiers_list, extend_location(location, "qualifiers")
                ),
            ),
            validate_many(
                *self.sources,
                locations=get_list_locations(
                    self.sources, extend_location(location, "sources")
                ),
            ),
            validate_many(
                *self.attributes_list,
                locations=get_list_locations(
                    self.attributes_list, extend_location(location, "attributes")
                ),
            ),
        )

        if kgraph is None:
            return warnings, errors

        if self.subject not in kgraph.edges:
            errors.append(
                SemanticValidationError(
                    f"Subject `{self.subject}` is not present in knowledge_graph.",
                    extend_location(location, "subject"),
                )
            )
        if self.object not in kgraph.edges:
            errors.append(
                SemanticValidationError(
                    f"Object `{self.object}` is not present in knowledge_graph.",
                    extend_location(location, "object"),
                )
            )

        has_primary = any(
            source.resource_role == ResourceRoleEnum.primary_knowledge_source
            for source in self.sources
        )
        if not has_primary:
            errors.append(
                SemanticValidationError(
                    "Edge is missing primary_knowledge_source.",
                    extend_location(location, "sources"),
                )
            )

        return warnings, errors

    def update(self, other: Edge) -> None:
        """Update the edge in-place with another edge."""
        if (not self.attributes) and other.attributes:
            self.attributes = other.attributes
        elif self.attributes and other.attributes:
            attrs = {attr.hash(): attr for attr in self.attributes}
            new_attrs = {
                attr.hash(): attr
                for attr in other.attributes
                # Avoid multiple KL/AT
                if attr.attribute_type_id
                not in (biolink("knowledge_level"), biolink("agent_type"))
            }
            self.attributes = list({**attrs, **new_attrs}.values())

        if (not self.sources) and other.sources:
            self.sources = other.sources
        elif self.sources and other.sources:
            sources = {source.hash(): source for source in self.sources}
            new_sources = {source.hash(): source for source in other.sources}

            # Roll in upstream_resource_ids from new sources that overlap
            for source_hash, source in sources.items():
                if new_source := new_sources.get(source_hash):
                    # Update new source so it overwrites the old source
                    new_source.update(source)
            self.sources = list({**sources, **new_sources}.values())

    def meets_attribute_constraints(
        self, constraints: list[AttributeConstraint]
    ) -> bool:
        """Check if all attribute constraints are satisfied by the edge's attributes."""
        attrs_by_type: dict[CURIE, list[Attribute]] = {}
        for attr in self.attributes_list:
            attrs_by_type.setdefault(attr.attribute_type_id, []).append(attr)
        return all(
            any(attr.meets_constraint(c) for attr in attrs_by_type.get(c.id, []))
            for c in constraints
        )

    def get_last_downstream_source(self) -> RetrievalSource | None:
        """Get the last/most downstream source in the chain."""
        upstreams = set(
            itertools.chain(
                *[source.upstream_resource_ids or [] for source in self.sources]
            )
        )
        return next(
            iter(
                source for source in self.sources if source.resource_id not in upstreams
            ),
            None,
        )

    def append_aggregator(self, source: Infores) -> None:
        """Append an aggregator source to the present chain with appropriate upstreams."""
        last_downstream = self.get_last_downstream_source()
        if last_downstream is None:
            raise ValueError("Provenance chain is invalid.")
        self.sources.append(
            RetrievalSource(
                resource_id=source,
                resource_role="aggregator_knowledge_source",
                upstream_resource_ids=[last_downstream.resource_id],
            )
        )
