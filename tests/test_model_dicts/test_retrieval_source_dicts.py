"""Tests for `RetrievalSourceDictUtil`, asserting parity with the model."""

from __future__ import annotations

from translator_tom.model_dicts.retrieval_source import (
    RetrievalSourceDict,
    RetrievalSourceDictUtil,
)
from translator_tom.models.retrieval_source import RetrievalSource


class TestListAccessors:
    def test_missing_returns_empty(self):
        source: RetrievalSourceDict = {
            "resource_id": "infores:x",
            "resource_role": "primary_knowledge_source",
        }
        assert RetrievalSourceDictUtil.upstream_resource_ids_list(source) == []
        assert RetrievalSourceDictUtil.source_record_urls_list(source) == []

    def test_populated(self):
        source: RetrievalSourceDict = {
            "resource_id": "infores:x",
            "resource_role": "aggregator_knowledge_source",
            "upstream_resource_ids": ["infores:y"],
            "source_record_urls": ["http://example.com"],
        }
        assert RetrievalSourceDictUtil.upstream_resource_ids_list(source) == [
            "infores:y"
        ]
        assert RetrievalSourceDictUtil.source_record_urls_list(source) == [
            "http://example.com"
        ]


class TestHashParity:
    def test_minimal(self):
        s = RetrievalSource(
            resource_id="infores:x", resource_role="primary_knowledge_source"
        )
        assert RetrievalSourceDictUtil.hash(s.to_dict()) == s.hash()

    def test_hash_ignores_non_identity_fields(self):
        # Only resource_id/resource_role feed the hash.
        a = RetrievalSource(
            resource_id="infores:x",
            resource_role="primary_knowledge_source",
            upstream_resource_ids=["infores:y"],
        )
        b = RetrievalSource(
            resource_id="infores:x", resource_role="primary_knowledge_source"
        )
        assert RetrievalSourceDictUtil.hash(a.to_dict()) == RetrievalSourceDictUtil.hash(
            b.to_dict()
        )


class TestUpdate:
    def _assert_parity(
        self, source: RetrievalSource, other: RetrievalSource
    ) -> None:
        source_dict = source.to_dict()
        source.update(other)
        RetrievalSourceDictUtil.update(source_dict, other.to_dict())
        # Merged upstream ids are built from a set, so compare order-independently.
        assert set(source_dict.get("upstream_resource_ids", [])) == set(
            source.upstream_resource_ids or []
        )

    def test_merges_upstream_ids(self):
        self._assert_parity(
            RetrievalSource(
                resource_id="infores:x",
                resource_role="aggregator_knowledge_source",
                upstream_resource_ids=["infores:a"],
            ),
            RetrievalSource(
                resource_id="infores:x",
                resource_role="aggregator_knowledge_source",
                upstream_resource_ids=["infores:b"],
            ),
        )

    def test_no_other_upstream_is_noop(self):
        source: RetrievalSourceDict = {
            "resource_id": "infores:x",
            "resource_role": "primary_knowledge_source",
        }
        RetrievalSourceDictUtil.update(
            source,
            {"resource_id": "infores:x", "resource_role": "primary_knowledge_source"},
        )
        assert "upstream_resource_ids" not in source
