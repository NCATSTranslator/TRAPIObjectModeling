from __future__ import annotations

import itertools
from typing import Annotated, ClassVar, Literal, cast

from pydantic import ConfigDict, Field
from typing_extensions import Self, override

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
from translator_tom.utils.hash import tomhash
from translator_tom.utils.object_base import TOMBase

__all__ = [
    "Edge",
    "KnowledgeGraph",
    "Node",
]


class KnowledgeGraph(TOMBase):
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

    @classmethod
    def new(cls) -> Self:
        """Return an empty instance, without having to pass required containers."""
        return cls.model_construct(nodes={}, edges={})

    def normalize(self) -> dict[EdgeID, EdgeID]:
        """Normalize the kgraph edge IDs and return a mapping of old:new.

        Mutates the kgraph; references to specific edges may become stale.
        """
        mapping = dict[EdgeID, EdgeID]()

        for edge_id in list(self.edges.keys()):
            edge = self.edges.pop(edge_id)
            new_id = edge.hash()
            mapping[edge_id] = new_id
            existing = self.edges.get(new_id)
            if existing is not None:
                # Copy on collision so .update()'s normalization doesn't mutate its `other`
                merged = existing.model_copy(deep=True)
                merged.update(edge)
                self.edges[new_id] = merged
            else:
                self.edges[new_id] = edge

        return mapping

    def update(
        self,
        other: KnowledgeGraph,
        pre_normalized: Literal["neither", "both", "self", "other"] = "neither",
        copy: bool = True,
    ) -> tuple[dict[EdgeID, EdgeID], dict[EdgeID, EdgeID]]:
        """Update the kgraph in-place using the other.

        Args:
            other: The other kgraph.
            pre_normalized: Which of self/other already have normalized (hash-keyed)
                edge IDs, to skip redundant normalization.
            copy: When True (default), `other` is copied to avoid mutation. Set to False for a mild performance improvement, when safe.

        Returns:
            `(self_mapping, other_mapping)` of old:new EdgeIDs, one per side that was
            normalized (empty otherwise). Kept separate because self/other may reuse an
            old edge ID for different edges.
        """
        self_mapping = dict[EdgeID, EdgeID]()
        other_mapping = dict[EdgeID, EdgeID]()
        if pre_normalized in ("neither", "other"):
            self_mapping = self.normalize()
        if pre_normalized in ("neither", "self"):
            # Normalize a shallow copy of the other dict so as not to modify the original
            # (model_construct skips validation)
            other = KnowledgeGraph.model_construct(
                nodes=dict(other.nodes), edges=dict(other.edges)
            )
            other_mapping = other.normalize()

        for node_id, node in other.nodes.items():
            if node_id in self.nodes:
                self.nodes[node_id].update(node)
                continue
            self.nodes[node_id] = node.model_copy(deep=True) if copy else node

        for edge_id, edge in other.edges.items():
            if edge_id in self.edges:
                self.edges[edge_id].update(edge)
                continue
            self.edges[edge_id] = edge.model_copy(deep=True) if copy else edge

        return self_mapping, other_mapping

    def _walk_results(
        self, aux_graphs: AuxiliaryGraphsDict, results: list[Result]
    ) -> tuple[set[EdgeID], set[CURIE]]:
        """Walk results to find immediately bound edges and nodes."""
        bound_edges = set[EdgeID]()
        bound_nodes = set[CURIE]()
        for result in results:
            for node_binding_set in result.node_bindings.values():
                bound_nodes.update([binding.id for binding in node_binding_set])
            for analysis in result.analyses:
                for aux_id in analysis.support_graphs_list:
                    bound_edges.update(aux_graphs[aux_id].edges)
                if isinstance(analysis, Analysis):
                    for edge_binding_set in analysis.edge_bindings.values():
                        bound_edges.update(binding.id for binding in edge_binding_set)
                else:
                    for path_binding in itertools.chain(
                        *(analysis.path_bindings.values())
                    ):
                        if path_binding.id in aux_graphs:
                            bound_edges.update(aux_graphs[path_binding.id].edges)
        return bound_edges, bound_nodes

    def prune(self, aux_graphs: AuxiliaryGraphsDict, results: list[Result]) -> None:
        """Remove any unused nodes or edges.

        Args:
          aux_graphs: Auxiliary graphs using this KG.
          results: Results list using this KG.

        Raises:
          KeyError: If nodes/edges are referenced that aren't present in the KG.
        """
        bound_edges, bound_nodes = self._walk_results(aux_graphs, results)

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
                edges_to_check.extend(aux_graphs[aux_graph_id].edges)

        # prior_edge_count = len(self.edges)
        # prior_node_count = len(self.nodes)

        self.edges = {edge_id: self.edges[edge_id] for edge_id in bound_edges}
        self.nodes = {curie: self.nodes[curie] for curie in bound_nodes}

        # pruned_edges = prior_edge_count - len(self.edges)
        # pruned_nodes = prior_node_count - len(self.nodes)


class Node(TOMBase):
    """A node in the KnowledgeGraph which represents some biomedical concept.

    Nodes are identified by the keys in the KnowledgeGraph Node mapping.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

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
        return tomhash((self.name, self.is_set))

    def meets_constraints(self, constraints: list[AttributeConstraint]) -> bool:
        """Check if all constraints are satisfied by the node's attributes."""
        return AttributeConstraint.set_met_by(constraints, self.attributes)

    def update(self, other: Node) -> None:
        """Update the node in-place with another node.

        Does not mutate `other`.
        """
        self.name = other.name or self.name
        self.categories = list(set(self.categories) | set(other.categories))

        if other.attributes:
            attrs = {attr.hash(): attr for attr in self.attributes}
            for attr in other.attributes:
                attrs[attr.hash()] = attr.model_copy(deep=True)
            self.attributes = list(attrs.values())


class Edge(TOMBase):
    """A specification of the semantic relationship linking two concepts that are expressed as nodes in the knowledge "thought" graph resulting from a query upon the underlying knowledge source."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

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
    """A list of RetrievalSource objects that provide information
    about how a particular Information Resource served
    as a source from which the knowledge expressed in an Edge,
    or data used to generate this knowledge, was retrieved.
    """

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

    @property
    def support_graphs(self) -> list[AuxGraphID]:
        """Get the support graph IDs referenced by this edge."""
        support_graphs = list[AuxGraphID]()
        for attr in self.attributes_list:
            if attr.attribute_type_id == Biolink("support_graphs"):
                support_graphs.extend(cast(list[AuxGraphID], attr.value))
        return support_graphs

    @override
    def hash(self) -> str:
        return tomhash(
            (
                self.subject,
                self.object,
                self.predicate,
                frozenset(q.hash() for q in self.qualifiers_list),
                self.primary_knowledge_source.resource_id,
            )
        )

    def update(self, other: Edge) -> None:
        """Update the edge in-place with another edge.

        Does not mutate `other`.
        """
        if (not self.attributes) and other.attributes:
            self.attributes = [attr.model_copy(deep=True) for attr in other.attributes]
        elif self.attributes and other.attributes:
            attrs = {attr.hash(): attr for attr in self.attributes}
            kl_at = (Biolink("knowledge_level"), Biolink("agent_type"))
            for attr in other.attributes:
                # Avoid multiple KL/AT
                if attr.attribute_type_id in kl_at:
                    continue
                attrs[attr.hash()] = attr.model_copy(deep=True)
            self.attributes = list(attrs.values())

        if (not self.sources) and other.sources:
            self.sources = [source.model_copy(deep=True) for source in other.sources]
        elif self.sources and other.sources:
            sources = {source.hash(): source for source in self.sources}
            for other_source in other.sources:
                source_hash = other_source.hash()
                # update existing or take copy of other
                if existing := sources.get(source_hash):
                    existing.update(other_source)
                else:
                    sources[source_hash] = other_source.model_copy(deep=True)
            self.sources = list(sources.values())

    def meets_attribute_constraints(
        self, constraints: list[AttributeConstraint]
    ) -> bool:
        """Check if all attribute constraints are satisfied by the edge's attributes."""
        return AttributeConstraint.set_met_by(constraints, self.attributes_list)

    def meets_qualifier_constraints(
        self, constraints: list[QualifierConstraint]
    ) -> bool:
        """Check if the edge satisfies the qualifier constraints."""
        return QualifierConstraint.set_met_by(constraints, self.qualifiers_list)

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


KnowledgeGraph.model_rebuild()  # Don't defer model build
