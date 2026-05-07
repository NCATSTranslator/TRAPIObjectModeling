"""Tests for translator_tom.models.retrieval_source."""

import pytest
from pydantic import ValidationError

from translator_tom import RetrievalSource
from translator_tom.models.retrieval_source import ResourceRoleEnum


class TestResourceRoleEnum:
    @pytest.mark.parametrize(
        ("member", "value"),
        [
            (ResourceRoleEnum.primary_knowledge_source, "primary_knowledge_source"),
            (
                ResourceRoleEnum.aggregator_knowledge_source,
                "aggregator_knowledge_source",
            ),
            (ResourceRoleEnum.supporting_data_source, "supporting_data_source"),
        ],
    )
    def test_values(self, member: ResourceRoleEnum, value: str):
        assert member.value == value
        assert member == value


def _src(
    resource_id: str = "infores:foo",
    role: str = "primary_knowledge_source",
    upstream: list[str] | None = None,
    urls: list[str] | None = None,
) -> RetrievalSource:
    return RetrievalSource(
        resource_id=resource_id,
        resource_role=role,  # type: ignore[arg-type]
        upstream_resource_ids=upstream,
        source_record_urls=urls,
    )


class TestRetrievalSourceBasics:
    def test_required_fields(self):
        s = _src()
        assert s.resource_id == "infores:foo"
        assert s.resource_role == "primary_knowledge_source"
        assert s.upstream_resource_ids is None
        assert s.source_record_urls is None

    def test_invalid_role_rejected(self):
        with pytest.raises(ValidationError):
            RetrievalSource(
                resource_id="infores:foo",
                resource_role="not_a_role",  # type: ignore[arg-type]
            )


class TestListProperties:
    def test_upstream_resource_ids_list_when_none(self):
        assert _src().upstream_resource_ids_list == []

    def test_upstream_resource_ids_list_when_set(self):
        s = _src(upstream=["infores:a", "infores:b"])
        assert s.upstream_resource_ids_list == ["infores:a", "infores:b"]

    def test_source_record_urls_list_when_none(self):
        assert _src().source_record_urls_list == []

    def test_source_record_urls_list_when_set(self):
        s = _src(urls=["https://example.org/1"])
        assert s.source_record_urls_list == ["https://example.org/1"]


class TestRetrievalSourceHash:
    def test_only_depends_on_id_and_role(self):
        # upstream_resource_ids and source_record_urls are excluded from hash.
        a = _src(upstream=["infores:a"], urls=["https://x"])
        b = _src(upstream=["infores:b"])
        assert a.hash() == b.hash()

    def test_changes_with_resource_id(self):
        a = _src("infores:a")
        b = _src("infores:b")
        assert a.hash() != b.hash()

    def test_changes_with_role(self):
        a = _src(role="primary_knowledge_source")
        b = _src(role="aggregator_knowledge_source")
        assert a.hash() != b.hash()


class TestRetrievalSourceUpdate:
    def test_assigns_upstreams_when_self_empty(self):
        a = _src()
        b = _src(upstream=["infores:up"])
        a.update(b)
        assert a.upstream_resource_ids == ["infores:up"]

    def test_unions_upstreams_when_both_present(self):
        a = _src(upstream=["infores:a"])
        b = _src(upstream=["infores:b"])
        a.update(b)
        assert a.upstream_resource_ids is not None
        assert set(a.upstream_resource_ids) == {"infores:a", "infores:b"}

    def test_no_op_when_other_has_no_upstreams(self):
        a = _src(upstream=["infores:a"])
        b = _src()
        a.update(b)
        assert a.upstream_resource_ids == ["infores:a"]
