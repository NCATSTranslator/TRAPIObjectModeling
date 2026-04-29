from __future__ import annotations

import itertools
from typing import Annotated, ClassVar, Literal, Self, cast, override

from pydantic import ConfigDict, Field
from stablehash import stablehash

from translator_tom.models.analysis import Analysis
from translator_tom.models.attribute import Attribute, AttributeConstraint
from translator_tom.models.auxiliary_graph import AuxiliaryGraphsDict
from translator_tom.models.qualifier import Qualifier, QualifierConstraint
from translator_tom.models.result import Result
from translator_tom.models.retrieval_source import (
    ResourceRoleEnum,
    RetrievalSource,
)
from translator_tom.models.shared import (
    CURIE,
    AuxGraphID,
    EdgeID,
    Infores,
)
from translator_tom.utils.biolink import Biolink
from translator_tom.utils.object_base import TOMBaseObject


class KnowledgeGraph(TOMBaseObject):
    """The knowledge graph associated with a set of results.

    The instances of Node and Edge defining this graph represent instances of
    biolink:NamedThing (concept nodes) and biolink:Association
    (relationship edges) representing (Attribute) annotated knowledge
    returned from the knowledge sources and inference agents wrapped by
    the given TRAPI implementation.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")

    nodes: dict[CURIE, Node]
    """Dictionary of Node instances used in the KnowledgeGraph, referenced elsewhere in the TRAPI output by the dictionary key."""

    edges: dict[EdgeID, Edge]
    """Dictionary of Edge instances used in the KnowledgeGraph, referenced elsewhere in the TRAPI output by the dictionary key."""

    @classmethod
    def new(cls) -> Self:
        """Return an empty instance, without having to pass required containers."""
        return cls(nodes={}, edges={})

    def normalize(self) -> dict[EdgeID, EdgeID]:
        """Normalize the kgraph edge IDs and return a mapping of old:new."""
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

    def prune(self, aux_graphs: AuxiliaryGraphsDict, results: list[Result]) -> None:
        """Remove any unused nodes or edges."""
        bound_edges = set[EdgeID]()
        bound_nodes = set[CURIE]()
        for result in results:
            for node_binding_set in result.node_bindings.values():
                bound_nodes.update([binding.id for binding in node_binding_set])
            for analysis in result.analyses:
                if isinstance(analysis, Analysis):
                    for edge_binding_set in analysis.edge_bindings.values():
                        bound_edges.update([binding.id for binding in edge_binding_set])
                else:
                    for path_binding in itertools.chain(
                        *(analysis.path_bindings.values())
                    ):
                        if path_binding.id in aux_graphs:
                            bound_edges.update(aux_graphs[path_binding.id].edges)

        checked_edges = set[EdgeID]()
        edges_to_check = list(bound_edges)
        while len(edges_to_check) > 0:
            edge_id = edges_to_check.pop()

            # Avoid infinite loops if edge and aux graph reference each other
            if edge_id in checked_edges:
                continue
            checked_edges.add(edge_id)

            edge = self.edges[edge_id]

            bound_edges.add(edge_id)
            bound_nodes.add(edge.subject)
            bound_nodes.add(edge.object)

            edge_aux_graphs = next(
                (
                    attr
                    for attr in edge.attributes_list
                    if attr.attribute_type_id == "biolink:support_graphs"
                ),
                None,
            )
            if edge_aux_graphs is None:
                continue
            # Have to cast because support graphs always has value of type list[str]
            # But attribute value is generally of type Any
            for aux_graph_id in cast(list[str], edge_aux_graphs.value):
                edges_to_check.extend(edge for edge in aux_graphs[aux_graph_id].edges)

        # prior_edge_count = len(self.edges)
        # prior_node_count = len(self.nodes)

        self.edges = {edge_id: self.edges[edge_id] for edge_id in bound_edges}
        self.nodes = {curie: self.nodes[curie] for curie in bound_nodes}

        # pruned_edges = prior_edge_count - len(self.edges)
        # pruned_nodes = prior_node_count - len(self.nodes)


class Node(TOMBaseObject):
    """A node in the KnowledgeGraph which represents some biomedical concept.

    Nodes are identified by the keys in the KnowledgeGraph Node mapping.
    """

    name: str | None = None
    """Formal name of the entity."""

    categories: Annotated[list[Biolink.Entity], Field(min_length=1)]
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
        # Categories and attributes shouldn't matter; what makes a node unique is its ID
        # name and is_set sort of naturally follow.
        # Either way, we don't merge nodes by hash, rather we do by index.
        return stablehash((self.name, self.is_set)).hexdigest()

    def meets_constraints(self, constraints: list[AttributeConstraint]) -> bool:
        """Check if all constraints are satisfied by the node's attributes."""
        attrs_by_type: dict[CURIE, list[Attribute]] = {}
        for attr in self.attributes:
            attrs_by_type.setdefault(attr.attribute_type_id, []).append(attr)
        return all(
            any(c.met_by(attr) for attr in attrs_by_type.get(c.id, []))
            for c in constraints
        )

    def update(self, other: Node) -> None:
        """Update the node in-place with another node."""
        self.name = other.name or self.name
        self.categories = list(set(self.categories) | set(other.categories))

        if other.attributes:
            attrs = {attr.hash(): attr for attr in self.attributes}
            new_attrs = {attr.hash(): attr for attr in other.attributes}
            self.attributes = list({**attrs, **new_attrs}.values())


class Edge(TOMBaseObject):
    """A specification of the semantic relationship linking two concepts that are expressed as nodes in the knowledge "thought" graph resulting from a query upon the underlying knowledge source."""

    predicate: Biolink.Predicate
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

    @property
    def last_downstream_source(self) -> RetrievalSource | None:
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

    @property
    def is_self_edge(self) -> bool:
        """Check if the edge is a self-edge."""
        return self.subject == self.object

    @override
    def hash(self) -> str:
        return stablehash(
            (
                self.subject,
                self.object,
                self.predicate,
                frozenset(q.hash() for q in self.qualifiers_list),
                self.primary_knowledge_source.resource_id,
            )
        ).hexdigest()

    def update(self, other: Edge) -> None:
        """Update the edge in-place with another edge."""
        if (not self.attributes) and other.attributes:
            self.attributes = other.attributes
        elif self.attributes and other.attributes:
            attrs = {attr.hash(): attr for attr in self.attributes}
            kl_at = (Biolink("knowledge_level"), Biolink("agent_type"))
            for attr in other.attributes:
                # Avoid multiple KL/AT
                if attr.attribute_type_id in kl_at:
                    continue
                attrs[attr.hash()] = attr
            self.attributes = list(attrs.values())

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
        if len(constraints) == 0:
            return True
        elif len(self.attributes_list) == 0:
            return False

        attrs_by_type: dict[CURIE, list[Attribute]] = {}
        for attr in self.attributes_list:
            attrs_by_type.setdefault(attr.attribute_type_id, []).append(attr)
        return all(
            all(c.met_by(attr) for attr in attrs_by_type.get(c.id, []))
            for c in constraints
        )

    def meets_qualifer_constraints(
        self, constraints: list[QualifierConstraint]
    ) -> bool:
        """Check if the edge satisfies the qualifier constraints."""
        if len(constraints) == 0:
            return True
        elif len(self.qualifiers_list) == 0:
            return False

        return any(
            constraint.met_by(self.qualifiers_list) for constraint in constraints
        )

    def append_aggregator(self, source: Infores) -> None:
        """Append an aggregator source to the present chain with appropriate upstreams."""
        last_downstream = self.last_downstream_source
        if last_downstream is None:
            raise ValueError("Provenance chain is invalid.")
        self.sources.append(
            RetrievalSource(
                resource_id=source,
                resource_role="aggregator_knowledge_source",
                upstream_resource_ids=[last_downstream.resource_id],
            )
        )
