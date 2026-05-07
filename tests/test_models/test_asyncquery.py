"""Tests for translator_tom.models.asyncquery."""

import pytest
from pydantic import ValidationError

from translator_tom import (
    AsyncQuery,
    AsyncQueryResponse,
    AsyncQueryStatusResponse,
    LogEntry,
    Message,
    Query,
)


class TestAsyncQuery:
    def test_inherits_from_query(self):
        a = AsyncQuery(message=Message(), callback="https://example.org/cb")
        assert isinstance(a, Query)
        assert a.callback == "https://example.org/cb"

    def test_callback_required(self):
        with pytest.raises(ValidationError):
            AsyncQuery(message=Message())  # type: ignore[call-arg]

    def test_inherits_query_defaults(self):
        a = AsyncQuery(message=Message(), callback="https://example.org/cb")
        assert a.bypass_cache is False
        assert a.workflow is None


class TestAsyncQueryResponse:
    def test_required_job_id(self):
        r = AsyncQueryResponse(job_id="abc123")
        assert r.job_id == "abc123"
        assert r.status is None
        assert r.description is None

    def test_full_construction(self):
        r = AsyncQueryResponse(
            job_id="abc123", status="Accepted", description="ok"
        )
        assert r.status == "Accepted"
        assert r.description == "ok"

    def test_job_id_required(self):
        with pytest.raises(ValidationError):
            AsyncQueryResponse()  # type: ignore[call-arg]


class TestAsyncQueryStatusResponse:
    def test_required_fields(self):
        r = AsyncQueryStatusResponse(
            status="Running",
            description="working",
            logs=[LogEntry.new("hello")],
        )
        assert r.status == "Running"
        assert r.response_url is None

    def test_logs_min_length_enforced(self):
        with pytest.raises(ValidationError):
            AsyncQueryStatusResponse(
                status="Running", description="working", logs=[]
            )

    def test_with_response_url(self):
        r = AsyncQueryStatusResponse(
            status="Completed",
            description="done",
            logs=[LogEntry.new("hello")],
            response_url="https://example.org/r",
        )
        assert r.response_url == "https://example.org/r"
