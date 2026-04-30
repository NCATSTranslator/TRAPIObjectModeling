from __future__ import annotations

from typing import Annotated, ClassVar, Self

from pydantic import ConfigDict, Field

from translator_tom.models.attribute import AttributeConstraint
from translator_tom.models.meta_attribute import MetaAttribute
from translator_tom.models.meta_qualifier import MetaQualifier
from translator_tom.models.qualifier import QualifierConstraint
from translator_tom.models.shared import (
    CURIE,
    KnowledgeType,
)
from translator_tom.utils.biolink import Biolink
from translator_tom.utils.object_base import TOMBaseObject


class MetaKnowledgeGraph(TOMBaseObject):
    """Knowledge-map representation of this TRAPI web service.

    The meta knowledge graph is composed of the union of most specific categories
    and predicates for each node and edge.
    """

    nodes: dict[Biolink.Entity, MetaNode]
    """Collection of the most specific node categories provided by this TRAPI web service, indexed by Biolink class CURIEs.

    A node category is only exposed here if there is
    node for which that is the most specific category available.
    """

    edges: list[MetaEdge]
    """List of the most specific edges/predicates provided by this TRAPI web service.

    A predicate is only exposed here if there is an edge
    for which the predicate is the most specific available.
    """

    @classmethod
    def new(cls) -> Self:
        """Return an empty instance, without having to pass required containers."""
        return cls(nodes={}, edges=[])


class MetaNode(TOMBaseObject):
    """Description of a node category provided by this TRAPI web service."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    id_prefixes: Annotated[list[str], Field(min_length=1)]
    """List of CURIE prefixes for the node category that this TRAPI web service understands and accepts on the input."""

    attributes: list[MetaAttribute] | None = None
    """Node attributes provided by this TRAPI web service."""

    @property
    def attributes_list(self) -> list[MetaAttribute]:
        """Get the meta attributes as a guaranteed list, even if they are represented as None."""
        return self.attributes if self.attributes is not None else []

    def update(self, other: MetaNode) -> None:
        """Update the meta edge in-place with another meta node."""
        self.id_prefixes = list(set(self.id_prefixes) | set(other.id_prefixes))

        if (not self.attributes) and other.attributes:
            self.attributes = other.attributes
        elif self.attributes and other.attributes:
            MetaAttribute.merge_attribute_lists(self.attributes, other.attributes)


class MetaEdge(TOMBaseObject):
    """Edge in a meta knowledge map describing relationship between a subject Biolink class and an object Biolink class."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    subject: Biolink.Entity
    """Subject node category of this relationship edge."""

    predicate: Biolink.Predicate
    """Biolink relationship between the subject and object categories."""

    object: Biolink.Entity
    """Object node category of this relationship edge."""

    knowledge_types: Annotated[list[KnowledgeType] | None, Field(min_length=1)] = None
    """A list of knowledge_types that are supported by the service.

    If the knowledge_types is null, this means that only 'lookup'
    is supported. Currently allowed values are 'lookup' or 'inferred'.
    """

    attributes: list[MetaAttribute] | None = None
    """Edge attributes provided by this TRAPI web service."""

    qualifiers: list[MetaQualifier] | None = None
    """Qualifiers that are possible to be found on this edge type."""

    association: Biolink.Entity | None = None
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
    def knowledge_types_list(self) -> list[KnowledgeType]:
        """Get the knowledge types as a guaranteed list, even if they are represented as None."""
        return self.knowledge_types if self.knowledge_types is not None else []

    @property
    def attributes_list(self) -> list[MetaAttribute]:
        """Get the meta attributes as a guaranteed list, even if they are represented as None."""
        return self.attributes if self.attributes is not None else []

    @property
    def qualifiers_list(self) -> list[MetaQualifier]:
        """Get the meta qualifiers as a guaranteed list, even if they are represented as None."""
        return self.qualifiers if self.qualifiers is not None else []

    def update(self, other: MetaEdge) -> None:
        """Update the meta edge in-place with another meta edge."""
        if (not self.knowledge_types) and other.knowledge_types:
            self.knowledge_types = other.knowledge_types
        elif self.knowledge_types and other.knowledge_types:
            self.knowledge_types = list(
                set(self.knowledge_types_list) | set(other.knowledge_types_list)
            )

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

        if not other.qualifiers:
            return
        if not self.qualifiers:
            self.qualifiers = other.qualifiers
            return

        quals_by_type = {qual.qualifier_type_id: qual for qual in self.qualifiers}
        new_quals_by_type = {qual.qualifier_type_id: qual for qual in other.qualifiers}

        for type_id, qual in new_quals_by_type.items():
            if type_id in quals_by_type:
                merged = list(
                    set(quals_by_type[type_id].applicable_values_list)
                    | set(qual.applicable_values_list)
                )
                if len(merged) > 0:
                    quals_by_type[type_id].applicable_values = merged
            else:
                quals_by_type[type_id] = qual

        self.qualifiers = list(quals_by_type.values())

    def meets_attribute_constraints(
        self, constraints: list[AttributeConstraint]
    ) -> bool:
        """Check if all attribute constraints are satisfied by the meta edge's attributes."""
        if len(constraints) == 0:
            return True
        elif len(self.attributes_list) == 0:
            return False

        attrs_by_type: dict[CURIE, list[MetaAttribute]] = {}
        for attr in self.attributes_list:
            attrs_by_type.setdefault(attr.attribute_type_id, []).append(attr)
        return all(
            any(c.met_by(attr) for attr in attrs_by_type.get(c.id, []))
            for c in constraints
        )

    def meets_qualifier_constraints(
        self, constraints: list[QualifierConstraint]
    ) -> bool:
        """Check if the meta edge satisfies the qualifier constraints."""
        if len(constraints) == 0:
            return True
        elif len(self.qualifiers_list) == 0:
            return False

        return any(
            constraint.met_by(self.qualifiers_list) for constraint in constraints
        )
