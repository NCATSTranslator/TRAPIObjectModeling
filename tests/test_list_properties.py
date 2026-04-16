"""Tests for _list convenience properties on optional list fields."""

from trapi_object_modeling.models.meta_attribute import MetaAttribute
from trapi_object_modeling.models.meta_knowledge_graph import MetaEdge
from trapi_object_modeling.models.meta_qualifier import MetaQualifier
from trapi_object_modeling.models.query_graph import QNode
from trapi_object_modeling.models.retrieval_source import RetrievalSource
from trapi_object_modeling.models.workflow_operations import (
    AnnotateEdgesParameters,
    AnnotateNodesParameters,
)


class TestMetaAttributeOriginalAttributeNamesList:
    def test_none_returns_empty(self) -> None:
        obj = MetaAttribute(attribute_type_id="biolink:p_value", original_attribute_names=None)
        assert obj.original_attribute_names_list == []

    def test_populated_returns_list(self) -> None:
        names = ["pvalue", "p-value"]
        obj = MetaAttribute(attribute_type_id="biolink:p_value", original_attribute_names=names)
        assert obj.original_attribute_names_list == names


class TestMetaEdgeKnowledgeTypesList:
    def test_none_returns_empty(self) -> None:
        obj = MetaEdge(subject="biolink:Gene", predicate="biolink:related_to", object="biolink:Gene")
        assert obj.knowledge_types_list == []

    def test_populated_returns_list(self) -> None:
        obj = MetaEdge(
            subject="biolink:Gene",
            predicate="biolink:related_to",
            object="biolink:Gene",
            knowledge_types=["lookup"],
        )
        assert obj.knowledge_types_list == ["lookup"]


class TestMetaQualifierApplicableValuesList:
    def test_none_returns_empty(self) -> None:
        obj = MetaQualifier(qualifier_type_id="biolink:object_aspect_qualifier")
        assert obj.applicable_values_list == []

    def test_populated_returns_list(self) -> None:
        vals = ["activity", "expression"]
        obj = MetaQualifier(qualifier_type_id="biolink:object_aspect_qualifier", applicable_values=vals)
        assert obj.applicable_values_list == vals


class TestQNodeIdsList:
    def test_none_returns_empty(self) -> None:
        obj = QNode()
        assert obj.ids_list == []

    def test_populated_returns_list(self) -> None:
        ids = ["NCBIGene:1234", "NCBIGene:5678"]
        obj = QNode(ids=ids)
        assert obj.ids_list == ids


class TestRetrievalSourceUpstreamResourceIdsList:
    def test_none_returns_empty(self) -> None:
        obj = RetrievalSource(resource_id="infores:molepro", resource_role="primary_knowledge_source")
        assert obj.upstream_resource_ids_list == []

    def test_populated_returns_list(self) -> None:
        ids = ["infores:chembl", "infores:drugbank"]
        obj = RetrievalSource(
            resource_id="infores:molepro",
            resource_role="primary_knowledge_source",
            upstream_resource_ids=ids,
        )
        assert obj.upstream_resource_ids_list == ids


class TestRetrievalSourceSourceRecordUrlsList:
    def test_none_returns_empty(self) -> None:
        obj = RetrievalSource(resource_id="infores:molepro", resource_role="primary_knowledge_source")
        assert obj.source_record_urls_list == []

    def test_populated_returns_list(self) -> None:
        urls = ["https://example.com/record1"]
        obj = RetrievalSource(
            resource_id="infores:molepro",
            resource_role="primary_knowledge_source",
            source_record_urls=urls,
        )
        assert obj.source_record_urls_list == urls


class TestAnnotateEdgesParametersAttributesList:
    def test_none_returns_empty(self) -> None:
        obj = AnnotateEdgesParameters()
        assert obj.attributes_list == []

    def test_populated_returns_list(self) -> None:
        obj = AnnotateEdgesParameters(attributes=["pmids"])
        assert obj.attributes_list == ["pmids"]


class TestAnnotateNodesParametersAttributesList:
    def test_none_returns_empty(self) -> None:
        obj = AnnotateNodesParameters(attributes=None)
        assert obj.attributes_list == []

    def test_populated_returns_list(self) -> None:
        obj = AnnotateNodesParameters(attributes=["pmids"])
        assert obj.attributes_list == ["pmids"]
