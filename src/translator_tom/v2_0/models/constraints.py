from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Annotated, Literal

from pydantic import Field

from translator_tom.utils.biolink import Biolink
from translator_tom.utils.object_base import TOMBase
from translator_tom.utils.shared import CURIE
from translator_tom.v2_0.models.attribute import AttributeConstraint
from translator_tom.v2_0.models.qualifier import Qualifier, QualifierSetConstraint
from translator_tom.v2_0.models.retrieval_source import (
    ResourceRoleEnum,
    RetrievalSource,
)

if TYPE_CHECKING:
    from translator_tom.v2_0.models.knowledge_graph import Edge

__all__ = [
    "AgentTypeConstraint",
    "AllowDenyConstraint",
    "AllowDenyConstraintBehavior",
    "AllowDenyConstraintBehaviorEnum",
    "KnowledgeLevelConstraint",
    "QEdgeConstraints",
    "SourceConstraint",
]

AllowDenyConstraintBehavior = Literal["ALLOW", "DENY"]


class AllowDenyConstraintBehaviorEnum(str, Enum):
    """Indicates how an AllowDenyConstraint MUST be interpreted."""

    ALLOW = "ALLOW"
    """ANY (at least 1) of the given values MUST appear in the constrained property in order for it to meet the constraint (OR relationship)."""

    DENY = "DENY"
    """ALL of the given values MUST NOT appear in the constrained property in order for it to meet the constraint (NOT (x OR y) relationship)."""


class AllowDenyConstraint(TOMBase):
    """A list of values which are to either be allowed or denied.

    If `behavior` is set to "ALLOW", then ANY (at least 1) of the given values
    MUST appear in the constrained property in order for it to meet the
    constraint (OR relationship).
    If `behavior` is set to "DENY", then ALL of the given values MUST NOT
    appear in the constrained property in order for it to meet the constraint
    (NOT (x OR y) relationship).
    """

    behavior: AllowDenyConstraintBehavior
    """The behavior mode of the constraint."""

    values: Annotated[list[str], Field(min_length=1)]
    """The values to allow/deny."""


class KnowledgeLevelConstraint(AllowDenyConstraint):
    """An AllowDenyConstraint that constrains the knowledge_level of a bound Edge."""

    def met_by(self, knowledge_level: str) -> bool:
        """Check if the given knowledge_level satisfies the constraint.

        A constraint value's biolink descendants count as included (hierarchy expansion).
        """
        allowed = Biolink.expand_permissible_values(
            "KnowledgeLevelEnum", frozenset(self.values)
        )
        present = knowledge_level in allowed
        return present if self.behavior == "ALLOW" else not present


class AgentTypeConstraint(AllowDenyConstraint):
    """An AllowDenyConstraint that constrains the agent_type of a bound Edge."""

    def met_by(self, agent_type: str) -> bool:
        """Check if the given agent_type satisfies the constraint.

        A constraint value's biolink descendants count as included (hierarchy expansion).
        """
        allowed = Biolink.expand_permissible_values(
            "AgentTypeEnum", frozenset(self.values)
        )
        present = agent_type in allowed
        return present if self.behavior == "ALLOW" else not present


class SourceConstraint(AllowDenyConstraint):
    """An AllowDenyConstraint that constrains the knowledge sources (resource_id) of a bound Edge."""

    values: Annotated[list[CURIE], Field(min_length=1)]
    """These SHOULD be infores CURIEs, so this is a subschema that is more stringent than the one in AllowDenyConstraint."""

    primary_only: bool = False
    """When set to `false` (the default), the ALLOW/DENY constraint of `values` applies to ALL RetrievalSources in the sources of the bound Edge.

    When set to `true`, the constraint ONLY applies to the
    RetrievalSource with the resource_role primary_knowledge_source.
    """

    def met_by(self, sources: list[RetrievalSource]) -> bool:
        """Whether a bound Edge's sources satisfy this ALLOW/DENY constraint.

        When `primary_only` is set, only the primary_knowledge_source is considered.
        """
        if self.primary_only:
            resource_ids = {
                source.resource_id
                for source in sources
                if source.resource_role == ResourceRoleEnum.primary_knowledge_source
            }
        else:
            resource_ids = {source.resource_id for source in sources}
        present = bool(resource_ids & set(self.values))
        return present if self.behavior == "ALLOW" else not present


class QEdgeConstraints(TOMBase):
    """A subschema for constraints that may be placed on a given QEdge.

    ALL edges bound to the given QEdge MUST conform to ALL given constraints;
    underlying edges (such as those appearing in supporting graphs)
    are not required to conform to the given constraints.
    """

    knowledge_level: KnowledgeLevelConstraint | None = None
    """A constraint defining knowledge_level values which are either allowed or denied on bound edges.

    Provided string(s) MUST be a valid biolink knowledge_level value.
    (See https://biolink.github.io/biolink-model/KnowledgeLevelEnum/)
    """

    agent_type: AgentTypeConstraint | None = None
    """A constraint defining agent_type values which are either allowed or denied on bound edges.

    Provided string(s) MUST be a valid biolink agent_type value.
    (See https://biolink.github.io/biolink-model/AgentTypeEnum/)
    """

    attributes: Annotated[list[AttributeConstraint], Field(min_length=1)] | None = None
    """A list of attribute constraints applied to a query edge.

    If there are multiple items, they must all be true (equivalent
    to AND)
    """

    qualifiers: Annotated[list[QualifierSetConstraint], Field(min_length=1)] | None = (
        None
    )
    """A list of QualifierSetConstraints applied to a QEdge.

    If multiple QualifierSetConstraints are provided, there is an OR
    relationship between them. If the QEdge has multiple
    predicates or if the QNodes that correspond to the subject or
    object of this QEdge have multiple categories or multiple
    curies, then constraints.qualifiers MUST NOT be specified
    because these complex use cases are not supported at this time.
    """

    sources: SourceConstraint | None = None
    """A list of infores CURIEs which are either allowed or denied in the sources (resource_id) of the bound Edge.

    If `behavior` is set to "ALLOW", ANY (at least 1) of the given infores
    CURIEs MUST be present.
    If `behavior` is set to "DENY", then ALL given infores CURIEs MUST
    NOT be present.
    """

    @property
    def attributes_list(self) -> list[AttributeConstraint]:
        """Get the attribute constraints as a guaranteed list, even if they are represented as None."""
        return self.attributes if self.attributes is not None else []

    @property
    def qualifiers_list(self) -> list[QualifierSetConstraint]:
        """Get the qualifier set constraints as a guaranteed list, even if they are represented as None."""
        return self.qualifiers if self.qualifiers is not None else []

    def get_inverse(self) -> QEdgeConstraints:
        """Return a (SPO) inverse of these constraints, for reversing edges.

        Directional attribute and qualifier constraints are flipped;
        knowledge_level, agent_type, and sources are direction-agnostic and
        pass through unchanged.
        """
        return QEdgeConstraints(
            knowledge_level=(
                self.knowledge_level.model_copy()
                if self.knowledge_level is not None
                else None
            ),
            agent_type=(
                self.agent_type.model_copy() if self.agent_type is not None else None
            ),
            sources=self.sources.model_copy() if self.sources is not None else None,
            attributes=(
                [ac.get_inverse() for ac in self.attributes]
                if self.attributes
                else None
            ),
            qualifiers=(
                [Qualifier.get_constraint_inverse(q) for q in self.qualifiers]
                if self.qualifiers
                else None
            ),
        )

    def met_by(self, edge: Edge) -> bool:
        """Whether a bound Edge satisfies all of these constraints."""
        return edge.meets_constraints(self)
