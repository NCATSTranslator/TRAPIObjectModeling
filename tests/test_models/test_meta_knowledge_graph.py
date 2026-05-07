"""Tests for translator_tom.models.meta_knowledge_graph."""

import pytest
from pydantic import ValidationError

from translator_tom import (
    AttributeConstraint,
    MetaAttribute,
    MetaEdge,
    MetaKnowledgeGraph,
    MetaNode,
    MetaQualifier,
    Qualifier,
    QualifierConstraint,
)


# ============================================================================
# MetaKnowledgeGraph
# ============================================================================


class TestMetaKnowledgeGraphNew:
    def test_new_empty(self):
        mkg = MetaKnowledgeGraph.new()
        assert mkg.nodes == {}
        assert mkg.edges == []


# ============================================================================
# MetaNode
# ============================================================================


class TestMetaNodeBasics:
    def test_required_field(self):
        n = MetaNode(id_prefixes=["NCBIGene"])
        assert n.id_prefixes == ["NCBIGene"]
        assert n.attributes is None

    def test_id_prefixes_min_length_enforced(self):
        with pytest.raises(ValidationError):
            MetaNode(id_prefixes=[])

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            MetaNode(id_prefixes=["X"], bogus="x")  # type: ignore[call-arg]


class TestMetaNodeAttributesList:
    def test_returns_empty_when_none(self):
        assert MetaNode(id_prefixes=["X"]).attributes_list == []

    def test_returns_list_when_set(self):
        ma = MetaAttribute(attribute_type_id="biolink:foo")
        assert MetaNode(id_prefixes=["X"], attributes=[ma]).attributes_list == [ma]


class TestMetaNodeUpdate:
    def test_unions_id_prefixes(self):
        a = MetaNode(id_prefixes=["NCBIGene"])
        b = MetaNode(id_prefixes=["HGNC", "NCBIGene"])
        a.update(b)
        assert set(a.id_prefixes) == {"NCBIGene", "HGNC"}

    def test_assigns_attributes_when_self_empty(self):
        a = MetaNode(id_prefixes=["X"])
        b = MetaNode(
            id_prefixes=["X"], attributes=[MetaAttribute(attribute_type_id="biolink:foo")]
        )
        a.update(b)
        assert a.attributes is not None
        assert len(a.attributes) == 1

    def test_merges_attributes_when_both_present(self):
        a = MetaNode(
            id_prefixes=["X"], attributes=[MetaAttribute(attribute_type_id="biolink:a")]
        )
        b = MetaNode(
            id_prefixes=["X"], attributes=[MetaAttribute(attribute_type_id="biolink:b")]
        )
        a.update(b)
        assert a.attributes is not None
        assert len(a.attributes) == 2


# ============================================================================
# MetaEdge
# ============================================================================


def _meta_edge(**kwargs: object) -> MetaEdge:
    defaults: dict[str, object] = {
        "subject": "biolink:Gene",
        "predicate": "biolink:related_to",
        "object": "biolink:Disease",
    }
    defaults.update(kwargs)
    return MetaEdge(**defaults)  # type: ignore[arg-type]


class TestMetaEdgeBasics:
    def test_required_fields(self):
        e = _meta_edge()
        assert e.subject == "biolink:Gene"
        assert e.predicate == "biolink:related_to"
        assert e.object == "biolink:Disease"
        assert e.knowledge_types is None
        assert e.attributes is None
        assert e.qualifiers is None
        assert e.association is None

    def test_knowledge_types_min_length_enforced(self):
        with pytest.raises(ValidationError):
            _meta_edge(knowledge_types=[])

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            _meta_edge(bogus="x")


class TestMetaEdgeListProperties:
    def test_knowledge_types_list_when_none(self):
        assert _meta_edge().knowledge_types_list == []

    def test_attributes_list_when_none(self):
        assert _meta_edge().attributes_list == []

    def test_qualifiers_list_when_none(self):
        assert _meta_edge().qualifiers_list == []


class TestMetaEdgeUpdate:
    def test_assigns_knowledge_types_when_self_empty(self):
        a = _meta_edge()
        b = _meta_edge(knowledge_types=["lookup"])
        a.update(b)
        assert a.knowledge_types == ["lookup"]

    def test_unions_knowledge_types(self):
        a = _meta_edge(knowledge_types=["lookup"])
        b = _meta_edge(knowledge_types=["inferred"])
        a.update(b)
        assert a.knowledge_types is not None
        assert set(a.knowledge_types) == {"lookup", "inferred"}

    def test_merges_attributes(self):
        a = _meta_edge(
            attributes=[MetaAttribute(attribute_type_id="biolink:a")]
        )
        b = _meta_edge(
            attributes=[MetaAttribute(attribute_type_id="biolink:b")]
        )
        a.update(b)
        assert a.attributes is not None
        assert len(a.attributes) == 2

    def test_skips_kl_at_dup(self):
        a = _meta_edge(
            attributes=[MetaAttribute(attribute_type_id="biolink:knowledge_level")]
        )
        b = _meta_edge(
            attributes=[MetaAttribute(attribute_type_id="biolink:knowledge_level")]
        )
        a.update(b)
        assert a.attributes is not None
        assert len(a.attributes) == 1

    def test_assigns_qualifiers_when_self_empty(self):
        a = _meta_edge()
        b = _meta_edge(
            qualifiers=[
                MetaQualifier(
                    qualifier_type_id="biolink:subject_aspect_qualifier",
                    applicable_values=["activity"],
                )
            ]
        )
        a.update(b)
        assert a.qualifiers is not None
        assert len(a.qualifiers) == 1

    def test_qualifier_no_op_when_other_empty(self):
        existing = MetaQualifier(
            qualifier_type_id="biolink:subject_aspect_qualifier",
            applicable_values=["activity"],
        )
        a = _meta_edge(qualifiers=[existing])
        b = _meta_edge()
        a.update(b)
        assert a.qualifiers == [existing]

    def test_qualifier_merges_applicable_values_for_same_type(self):
        a = _meta_edge(
            qualifiers=[
                MetaQualifier(
                    qualifier_type_id="biolink:subject_aspect_qualifier",
                    applicable_values=["activity"],
                )
            ]
        )
        b = _meta_edge(
            qualifiers=[
                MetaQualifier(
                    qualifier_type_id="biolink:subject_aspect_qualifier",
                    applicable_values=["abundance"],
                )
            ]
        )
        a.update(b)
        assert a.qualifiers is not None
        assert len(a.qualifiers) == 1
        assert set(a.qualifiers[0].applicable_values_list) == {
            "activity",
            "abundance",
        }

    def test_qualifier_appends_new_type(self):
        a = _meta_edge(
            qualifiers=[
                MetaQualifier(qualifier_type_id="biolink:subject_aspect_qualifier")
            ]
        )
        b = _meta_edge(
            qualifiers=[
                MetaQualifier(qualifier_type_id="biolink:object_aspect_qualifier")
            ]
        )
        a.update(b)
        assert a.qualifiers is not None
        types = {q.qualifier_type_id for q in a.qualifiers}
        assert types == {
            "biolink:subject_aspect_qualifier",
            "biolink:object_aspect_qualifier",
        }


class TestMetaEdgeMeetsAttributeConstraints:
    def test_no_constraints_returns_true(self):
        assert _meta_edge().meets_attribute_constraints([]) is True

    def test_with_no_attributes_returns_false(self):
        c = AttributeConstraint(
            id="biolink:foo", name="foo", operator="==", value=1
        )
        assert _meta_edge().meets_attribute_constraints([c]) is False

    def test_satisfied_when_id_matches_and_constraint_use_true(self):
        e = _meta_edge(
            attributes=[
                MetaAttribute(attribute_type_id="biolink:foo", constraint_use=True)
            ]
        )
        c = AttributeConstraint(
            id="biolink:foo", name="foo", operator="==", value=1
        )
        assert e.meets_attribute_constraints([c]) is True

    def test_unsatisfied_when_id_mismatch(self):
        e = _meta_edge(
            attributes=[
                MetaAttribute(attribute_type_id="biolink:foo", constraint_use=True)
            ]
        )
        c = AttributeConstraint(
            id="biolink:bar", name="bar", operator="==", value=1
        )
        assert e.meets_attribute_constraints([c]) is False


class TestMetaEdgeMeetsQualifierConstraints:
    def test_no_constraints_returns_true(self):
        assert _meta_edge().meets_qualifier_constraints([]) is True

    def test_with_no_qualifiers_returns_false(self):
        c = QualifierConstraint(
            qualifier_set=[
                Qualifier(
                    qualifier_type_id="biolink:subject_aspect_qualifier",
                    qualifier_value="activity",
                )
            ]
        )
        assert _meta_edge().meets_qualifier_constraints([c]) is False

    def test_satisfied(self):
        e = _meta_edge(
            qualifiers=[
                MetaQualifier(
                    qualifier_type_id="biolink:subject_aspect_qualifier",
                    applicable_values=["activity"],
                )
            ]
        )
        c = QualifierConstraint(
            qualifier_set=[
                Qualifier(
                    qualifier_type_id="biolink:subject_aspect_qualifier",
                    qualifier_value="activity",
                )
            ]
        )
        assert e.meets_qualifier_constraints([c]) is True
