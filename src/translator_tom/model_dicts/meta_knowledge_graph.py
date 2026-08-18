from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from translator_tom.model_dicts.attribute import (
    AttributeConstraintDict,
    AttributeConstraintDictUtil,
)
from translator_tom.model_dicts.meta_attribute import (
    MetaAttributeDict,
    MetaAttributeDictUtil,
)
from translator_tom.model_dicts.meta_qualifier import MetaQualifierDict
from translator_tom.model_dicts.qualifier import (
    QualifierDictUtil,
    QualifierSetConstraint,
)
from translator_tom.models.meta_knowledge_graph import (
    MetaEdge,
    MetaKnowledgeGraph,
    MetaNode,
    merged_applicable_values,
)
from translator_tom.models.shared import KnowledgeType
from translator_tom.utils.biolink import Biolink
from translator_tom.utils.dict_util_base import DictUtil

__all__ = [
    "MetaEdgeDict",
    "MetaEdgeDictUtil",
    "MetaKnowledgeGraphDict",
    "MetaKnowledgeGraphDictUtil",
    "MetaNodeDict",
    "MetaNodeDictUtil",
]


class MetaNodeDict(TypedDict):
    id_prefixes: list[str]
    attributes: NotRequired[list[MetaAttributeDict] | None]


class MetaNodeDictUtil(DictUtil[MetaNodeDict]):
    """Utility methods for `MetaNodeDict`, mirroring those on the `MetaNode` model."""

    _model = MetaNode

    @staticmethod
    def attributes_list(meta_node: MetaNodeDict) -> list[MetaAttributeDict]:
        """Get the meta attributes as a guaranteed list, even if they are represented as None."""
        attributes = meta_node.get("attributes")
        return attributes if attributes is not None else []

    @staticmethod
    def update(meta_node: MetaNodeDict, other: MetaNodeDict) -> None:
        """Update the meta node in-place with another meta node."""
        meta_node["id_prefixes"] = list(
            set(meta_node["id_prefixes"]) | set(other["id_prefixes"])
        )

        node_attrs = meta_node.get("attributes")
        other_attrs = other.get("attributes")
        if (not node_attrs) and other_attrs:
            meta_node["attributes"] = other_attrs
        elif node_attrs and other_attrs:
            MetaAttributeDictUtil.merge_attribute_lists(node_attrs, other_attrs)


class MetaEdgeDict(TypedDict):
    subject: Biolink.Entity
    predicate: Biolink.Predicate
    object: Biolink.Entity
    knowledge_types: NotRequired[list[KnowledgeType] | None]
    attributes: NotRequired[list[MetaAttributeDict] | None]
    qualifiers: NotRequired[list[MetaQualifierDict] | None]
    association: NotRequired[Biolink.Entity | None]


class MetaEdgeDictUtil(DictUtil[MetaEdgeDict]):
    """Utility methods for `MetaEdgeDict`, mirroring those on the `MetaEdge` model."""

    _model = MetaEdge

    @staticmethod
    def knowledge_types_list(meta_edge: MetaEdgeDict) -> list[KnowledgeType]:
        """Get the knowledge types as a guaranteed list, even if they are represented as None."""
        knowledge_types = meta_edge.get("knowledge_types")
        return knowledge_types if knowledge_types is not None else []

    @staticmethod
    def attributes_list(meta_edge: MetaEdgeDict) -> list[MetaAttributeDict]:
        """Get the meta attributes as a guaranteed list, even if they are represented as None."""
        attributes = meta_edge.get("attributes")
        return attributes if attributes is not None else []

    @staticmethod
    def qualifiers_list(meta_edge: MetaEdgeDict) -> list[MetaQualifierDict]:
        """Get the meta qualifiers as a guaranteed list, even if they are represented as None."""
        qualifiers = meta_edge.get("qualifiers")
        return qualifiers if qualifiers is not None else []

    @staticmethod
    def update(meta_edge: MetaEdgeDict, other: MetaEdgeDict) -> None:
        """Update the meta edge in-place with another meta edge."""
        edge_kt = meta_edge.get("knowledge_types")
        other_kt = other.get("knowledge_types")
        if (not edge_kt) and other_kt:
            meta_edge["knowledge_types"] = other_kt
        elif edge_kt and other_kt:
            meta_edge["knowledge_types"] = list(
                set(MetaEdgeDictUtil.knowledge_types_list(meta_edge))
                | set(MetaEdgeDictUtil.knowledge_types_list(other))
            )

        edge_attrs = meta_edge.get("attributes")
        other_attrs = other.get("attributes")
        if (not edge_attrs) and other_attrs:
            meta_edge["attributes"] = other_attrs
        elif edge_attrs and other_attrs:
            attrs = {MetaAttributeDictUtil.hash(attr): attr for attr in edge_attrs}
            kl_at = (Biolink("knowledge_level"), Biolink("agent_type"))
            for attr in other_attrs:
                # Avoid multiple KL/AT
                if attr["attribute_type_id"] in kl_at:
                    continue
                attrs[MetaAttributeDictUtil.hash(attr)] = attr
            meta_edge["attributes"] = list(attrs.values())

        other_quals = other.get("qualifiers")
        if not other_quals:
            return
        edge_quals = meta_edge.get("qualifiers")
        if not edge_quals:
            meta_edge["qualifiers"] = other_quals
            return

        quals_by_type = {qual["qualifier_type_id"]: qual for qual in edge_quals}
        new_quals_by_type = {qual["qualifier_type_id"]: qual for qual in other_quals}
        for type_id, qual in new_quals_by_type.items():
            if type_id in quals_by_type:
                MetaEdgeDictUtil._merge_applicable_values(quals_by_type[type_id], qual)
            else:
                quals_by_type[type_id] = qual

        meta_edge["qualifiers"] = list(quals_by_type.values())

    @staticmethod
    def _merge_applicable_values(
        existing: MetaQualifierDict, other: MetaQualifierDict
    ) -> None:
        """Merge `other`'s applicable_values into `existing` in place (None absorbs any list)."""
        merged = merged_applicable_values(
            existing.get("applicable_values"), other.get("applicable_values")
        )
        if merged is None:
            existing.pop("applicable_values", None)  # "all allowed": omit the key
        else:
            existing["applicable_values"] = merged

    @staticmethod
    def meets_attribute_constraints(
        meta_edge: MetaEdgeDict, constraints: list[AttributeConstraintDict]
    ) -> bool:
        """Check if all attribute constraints are satisfied by the meta edge's attributes."""
        return AttributeConstraintDictUtil.set_met_by(
            constraints, MetaEdgeDictUtil.attributes_list(meta_edge)
        )

    @staticmethod
    def meets_qualifier_constraints(
        meta_edge: MetaEdgeDict, constraints: list[QualifierSetConstraint]
    ) -> bool:
        """Check if the meta edge satisfies the qualifier constraints."""
        return QualifierDictUtil.constraint_set_met_by(
            constraints, MetaEdgeDictUtil.qualifiers_list(meta_edge)
        )


class MetaKnowledgeGraphDict(TypedDict):
    nodes: dict[Biolink.Entity, MetaNodeDict]
    edges: list[MetaEdgeDict]


class MetaKnowledgeGraphDictUtil(DictUtil[MetaKnowledgeGraphDict]):
    """Utility methods for `MetaKnowledgeGraphDict`, mirroring the `MetaKnowledgeGraph` model."""

    _model = MetaKnowledgeGraph

    @staticmethod
    def new() -> MetaKnowledgeGraphDict:
        """Return an empty instance, without having to pass required containers."""
        return {"nodes": {}, "edges": []}
