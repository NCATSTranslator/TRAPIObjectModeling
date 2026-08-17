"""Parity tests for the meta-knowledge-graph `*DictUtil` classes."""

from __future__ import annotations

from translator_tom.model_dicts.meta_knowledge_graph import (
    MetaEdgeDictUtil,
    MetaKnowledgeGraphDictUtil,
    MetaNodeDictUtil,
)
from translator_tom.models.attribute import AttributeConstraint
from translator_tom.models.meta_attribute import MetaAttribute
from translator_tom.models.meta_knowledge_graph import (
    MetaEdge,
    MetaKnowledgeGraph,
    MetaNode,
)
from translator_tom.models.meta_qualifier import MetaQualifier
from translator_tom.models.qualifier import Qualifier, QualifierConstraint

# ============================================================================
# MetaNode
# ============================================================================


class TestMetaNode:
    def test_attributes_list(self):
        node = MetaNode(
            id_prefixes=["CHEBI"], attributes=[MetaAttribute(attribute_type_id="x")]
        )
        assert MetaNodeDictUtil.attributes_list(node.to_dict()) == node.to_dict()[
            "attributes"
        ]

    def test_hash_parity(self):
        node = MetaNode(
            id_prefixes=["CHEBI", "PUBCHEM"],
            attributes=[MetaAttribute(attribute_type_id="biolink:x")],
        )
        assert MetaNodeDictUtil.hash(node.to_dict()) == node.hash()

    def test_update_parity(self):
        node = MetaNode(
            id_prefixes=["CHEBI"],
            attributes=[MetaAttribute(attribute_type_id="biolink:a")],
        )
        other = MetaNode(
            id_prefixes=["PUBCHEM"],
            attributes=[MetaAttribute(attribute_type_id="biolink:b")],
        )
        node_dict = node.to_dict()
        node.update(other)
        MetaNodeDictUtil.update(node_dict, other.to_dict())
        assert node_dict == node.to_dict()


# ============================================================================
# MetaEdge
# ============================================================================


def _meta_edge(**kwargs: object) -> MetaEdge:
    base: dict[str, object] = {
        "subject": "biolink:Gene",
        "predicate": "biolink:affects",
        "object": "biolink:Disease",
    }
    base.update(kwargs)
    return MetaEdge(**base)  # type: ignore[arg-type]


class TestMetaEdge:
    def test_list_accessors(self):
        edge = _meta_edge(knowledge_types=["lookup"])
        assert MetaEdgeDictUtil.knowledge_types_list(edge.to_dict()) == ["lookup"]
        assert MetaEdgeDictUtil.attributes_list(edge.to_dict()) == []
        assert MetaEdgeDictUtil.qualifiers_list(edge.to_dict()) == []

    def test_hash_parity(self):
        edge = _meta_edge(
            knowledge_types=["lookup"],
            attributes=[MetaAttribute(attribute_type_id="biolink:x")],
            qualifiers=[
                MetaQualifier(
                    qualifier_type_id="biolink:subject_aspect_qualifier",
                    applicable_values=["activity"],
                )
            ],
        )
        assert MetaEdgeDictUtil.hash(edge.to_dict()) == edge.hash()

    def test_update_parity(self):
        edge = _meta_edge(
            knowledge_types=["lookup"],
            attributes=[MetaAttribute(attribute_type_id="biolink:a")],
            qualifiers=[
                MetaQualifier(
                    qualifier_type_id="biolink:subject_aspect_qualifier",
                    applicable_values=["activity"],
                )
            ],
        )
        other = _meta_edge(
            knowledge_types=["inferred"],
            attributes=[MetaAttribute(attribute_type_id="biolink:b")],
            qualifiers=[
                MetaQualifier(
                    qualifier_type_id="biolink:subject_aspect_qualifier",
                    applicable_values=["abundance"],
                )
            ],
        )
        edge_dict = edge.to_dict()
        edge.update(other)
        MetaEdgeDictUtil.update(edge_dict, other.to_dict())
        # knowledge_types / applicable_values merge via sets; compare set-wise.
        assert set(edge_dict["knowledge_types"]) == set(edge.knowledge_types or [])
        assert MetaEdgeDictUtil.hash(edge_dict) == edge.hash()
        merged_values = {
            q["qualifier_type_id"]: set(q.get("applicable_values") or [])
            for q in edge_dict["qualifiers"]
        }
        model_values = {
            q.qualifier_type_id: set(q.applicable_values or [])
            for q in (edge.qualifiers or [])
        }
        assert merged_values == model_values

    def test_update_all_allowed_absorbs_concrete_parity(self):
        # applicable_values=None ("all allowed") must survive the merge on both sides,
        # not narrow to the concrete list. Asserts the absolute result, not just parity.
        for self_vals, other_vals in ((None, ["activity"]), (["activity"], None)):
            edge = _meta_edge(
                qualifiers=[
                    MetaQualifier(
                        qualifier_type_id="biolink:subject_aspect_qualifier",
                        applicable_values=self_vals,
                    )
                ]
            )
            other = _meta_edge(
                qualifiers=[
                    MetaQualifier(
                        qualifier_type_id="biolink:subject_aspect_qualifier",
                        applicable_values=other_vals,
                    )
                ]
            )
            edge_dict = edge.to_dict()
            edge.update(other)
            MetaEdgeDictUtil.update(edge_dict, other.to_dict())
            assert (edge.qualifiers or [])[0].applicable_values is None
            assert edge_dict["qualifiers"][0].get("applicable_values") is None
            assert MetaEdgeDictUtil.hash(edge_dict) == edge.hash()

    def test_meets_attribute_constraints_parity(self):
        edge = _meta_edge(attributes=[MetaAttribute(attribute_type_id="biolink:foo")])
        constraints = [
            AttributeConstraint(id="biolink:foo", name="Foo", operator="==", value=1)
        ]
        assert MetaEdgeDictUtil.meets_attribute_constraints(
            edge.to_dict(), [c.to_dict() for c in constraints]
        ) == edge.meets_attribute_constraints(constraints)

    def test_meets_qualifier_constraints_parity(self):
        edge = _meta_edge(
            qualifiers=[
                MetaQualifier(
                    qualifier_type_id="biolink:subject_aspect_qualifier",
                    applicable_values=["activity"],
                )
            ]
        )
        constraints = [
            QualifierConstraint(
                qualifier_set=[
                    Qualifier(
                        qualifier_type_id="biolink:subject_aspect_qualifier",
                        qualifier_value="activity",
                    )
                ]
            )
        ]
        assert MetaEdgeDictUtil.meets_qualifier_constraints(
            edge.to_dict(), [c.to_dict() for c in constraints]
        ) == edge.meets_qualifier_constraints(constraints)


# ============================================================================
# MetaKnowledgeGraph
# ============================================================================


class TestMetaKnowledgeGraph:
    def test_new(self):
        assert MetaKnowledgeGraphDictUtil.new() == MetaKnowledgeGraph.new().to_dict()
        assert MetaKnowledgeGraphDictUtil.new() == {"nodes": {}, "edges": []}

    def test_hash_parity(self):
        mkg = MetaKnowledgeGraph(
            nodes={"biolink:Gene": MetaNode(id_prefixes=["NCBIGene"])},
            edges=[_meta_edge()],
        )
        assert MetaKnowledgeGraphDictUtil.hash(mkg.to_dict()) == mkg.hash()


class TestMetaEdgeUpdateKlAtSkip:
    def test_update_skips_knowledge_level_and_agent_type(self):
        edge = _meta_edge(attributes=[MetaAttribute(attribute_type_id="biolink:a")])
        other = _meta_edge(
            attributes=[
                MetaAttribute(attribute_type_id="biolink:knowledge_level"),
                MetaAttribute(attribute_type_id="biolink:agent_type"),
                MetaAttribute(attribute_type_id="biolink:b"),
            ]
        )
        edge_dict = edge.to_dict()
        edge.update(other)
        MetaEdgeDictUtil.update(edge_dict, other.to_dict())
        assert edge_dict == edge.to_dict()
        types = {a["attribute_type_id"] for a in edge_dict.get("attributes", [])}
        assert "biolink:knowledge_level" not in types
        assert "biolink:agent_type" not in types
