from __future__ import annotations

from typing import TYPE_CHECKING, cast

from typing_extensions import NotRequired, TypedDict

from translator_tom.utils.biolink import Biolink
from translator_tom.utils.dict_util_base import DictUtil
from translator_tom.utils.shared import CURIE
from translator_tom.v2_0.model_dicts.attribute import (
    AttributeConstraintDict,
    AttributeConstraintDictUtil,
)
from translator_tom.v2_0.model_dicts.qualifier import (
    QualifierDictUtil,
    QualifierSetConstraint,
)
from translator_tom.v2_0.model_dicts.retrieval_source import RetrievalSourceDict
from translator_tom.v2_0.models.constraints import (
    AgentTypeConstraint,
    AllowDenyConstraint,
    AllowDenyConstraintBehavior,
    KnowledgeLevelConstraint,
    QEdgeConstraints,
    SourceConstraint,
)
from translator_tom.v2_0.models.retrieval_source import ResourceRoleEnum

if TYPE_CHECKING:
    from translator_tom.v2_0.model_dicts.knowledge_graph import EdgeDict

__all__ = [
    "AgentTypeConstraintDict",
    "AgentTypeConstraintDictUtil",
    "AllowDenyConstraintDict",
    "AllowDenyConstraintDictUtil",
    "KnowledgeLevelConstraintDict",
    "KnowledgeLevelConstraintDictUtil",
    "QEdgeConstraintsDict",
    "QEdgeConstraintsDictUtil",
    "SourceConstraintDict",
    "SourceConstraintDictUtil",
]


class AllowDenyConstraintDict(TypedDict):
    behavior: AllowDenyConstraintBehavior
    values: list[str]


class AllowDenyConstraintDictUtil(DictUtil[AllowDenyConstraintDict]):
    """Registration-only util for `AllowDenyConstraintDict`."""

    _model = AllowDenyConstraint


class KnowledgeLevelConstraintDict(AllowDenyConstraintDict):
    pass


class KnowledgeLevelConstraintDictUtil(DictUtil[KnowledgeLevelConstraintDict]):
    """Utility methods for `KnowledgeLevelConstraintDict`, mirroring the model."""

    _model = KnowledgeLevelConstraint

    @staticmethod
    def met_by(constraint: KnowledgeLevelConstraintDict, knowledge_level: str) -> bool:
        """Check if the given knowledge_level satisfies the constraint (with hierarchy expansion)."""
        allowed = Biolink.expand_permissible_values(
            "KnowledgeLevelEnum", frozenset(constraint["values"])
        )
        present = knowledge_level in allowed
        return present if constraint["behavior"] == "ALLOW" else not present


class AgentTypeConstraintDict(AllowDenyConstraintDict):
    pass


class AgentTypeConstraintDictUtil(DictUtil[AgentTypeConstraintDict]):
    """Utility methods for `AgentTypeConstraintDict`, mirroring the model."""

    _model = AgentTypeConstraint

    @staticmethod
    def met_by(constraint: AgentTypeConstraintDict, agent_type: str) -> bool:
        """Check if the given agent_type satisfies the constraint (with hierarchy expansion)."""
        allowed = Biolink.expand_permissible_values(
            "AgentTypeEnum", frozenset(constraint["values"])
        )
        present = agent_type in allowed
        return present if constraint["behavior"] == "ALLOW" else not present


class SourceConstraintDict(AllowDenyConstraintDict):
    values: list[CURIE]
    primary_only: NotRequired[bool]


class SourceConstraintDictUtil(DictUtil[SourceConstraintDict]):
    """Utility methods for `SourceConstraintDict`, mirroring the `SourceConstraint` model."""

    _model = SourceConstraint

    @staticmethod
    def met_by(
        constraint: SourceConstraintDict, sources: list[RetrievalSourceDict]
    ) -> bool:
        """Whether a bound Edge's sources satisfy this constraint (honoring primary_only)."""
        if constraint.get("primary_only", False):
            resource_ids = {
                source["resource_id"]
                for source in sources
                if source["resource_role"] == ResourceRoleEnum.primary_knowledge_source
            }
        else:
            resource_ids = {source["resource_id"] for source in sources}
        present = bool(resource_ids & set(constraint["values"]))
        return present if constraint["behavior"] == "ALLOW" else not present


class QEdgeConstraintsDict(TypedDict):
    knowledge_level: NotRequired[KnowledgeLevelConstraintDict | None]
    agent_type: NotRequired[AgentTypeConstraintDict | None]
    attributes: NotRequired[list[AttributeConstraintDict] | None]
    qualifiers: NotRequired[list[QualifierSetConstraint] | None]
    sources: NotRequired[SourceConstraintDict | None]


class QEdgeConstraintsDictUtil(DictUtil[QEdgeConstraintsDict]):
    """Utility methods for `QEdgeConstraintsDict`, mirroring those on the `QEdgeConstraints` model."""

    _model = QEdgeConstraints

    @staticmethod
    def attributes_list(
        constraints: QEdgeConstraintsDict,
    ) -> list[AttributeConstraintDict]:
        """Get the attribute constraints as a guaranteed list, even if they are represented as None."""
        attributes = constraints.get("attributes")
        return attributes if attributes is not None else []

    @staticmethod
    def qualifiers_list(
        constraints: QEdgeConstraintsDict,
    ) -> list[QualifierSetConstraint]:
        """Get the qualifier set constraints as a guaranteed list, even if they are represented as None."""
        qualifiers = constraints.get("qualifiers")
        return qualifiers if qualifiers is not None else []

    @staticmethod
    def get_inverse(constraints: QEdgeConstraintsDict) -> QEdgeConstraintsDict:
        """Return a (SPO) inverse of these constraints, for reversing edges.

        Directional attribute and qualifier constraints are flipped; knowledge_level,
        agent_type, and sources are direction-agnostic and pass through unchanged.
        """
        inverted = cast("QEdgeConstraintsDict", {})
        if (knowledge_level := constraints.get("knowledge_level")) is not None:
            inverted["knowledge_level"] = cast(
                "KnowledgeLevelConstraintDict", {**knowledge_level}
            )
        if (agent_type := constraints.get("agent_type")) is not None:
            inverted["agent_type"] = cast("AgentTypeConstraintDict", {**agent_type})
        if (sources := constraints.get("sources")) is not None:
            inverted["sources"] = cast("SourceConstraintDict", {**sources})
        if attributes := constraints.get("attributes"):
            inverted["attributes"] = [
                AttributeConstraintDictUtil.get_inverse(ac) for ac in attributes
            ]
        if qualifiers := constraints.get("qualifiers"):
            inverted["qualifiers"] = [
                QualifierDictUtil.get_constraint_inverse(q) for q in qualifiers
            ]
        return inverted

    @staticmethod
    def met_by(constraints: QEdgeConstraintsDict, edge: EdgeDict) -> bool:
        """Whether a bound Edge dict satisfies all of these constraints.

        Delegates to `EdgeDictUtil.meets_constraints`, which composes the per-constraint checks.
        """
        from translator_tom.v2_0.model_dicts.knowledge_graph import (  # noqa: PLC0415
            EdgeDictUtil,
        )

        return EdgeDictUtil.meets_constraints(edge, constraints)
