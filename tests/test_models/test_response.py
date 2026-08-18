"""Tests for translator_tom.models.response."""

import pytest
from pydantic import ValidationError

from translator_tom import LogEntry, Message, Response, workflow
from translator_tom.utils.config import TRAPI_CONFIG


class TestResponseBasics:
    def test_required_field(self):
        r = Response(message=Message())
        assert isinstance(r.message, Message)
        assert r.status is None
        assert r.description is None
        assert r.parameters is None
        assert r.logs is None
        assert r.logs_list == []
        assert r.workflow is None
        assert r.schema_version is None
        assert r.biolink_version is None

    def test_message_required(self):
        with pytest.raises(ValidationError):
            Response()  # type: ignore[call-arg]

    def test_logs_defaults_to_none(self):
        r = Response(message=Message())
        assert r.logs is None
        assert r.logs_list == []

    def test_logs_min_length_when_present(self):
        # logs is optional but an empty list is invalid (omit instead).
        with pytest.raises(ValidationError):
            Response(message=Message(), logs=[])


class TestResponseAddLog:
    def test_initializes_logs_when_absent(self):
        r = Response(message=Message())
        r.add_log(LogEntry.new("hello", level="INFO"))
        assert r.logs is not None
        assert len(r.logs) == 1

    def test_appends_to_existing_logs(self):
        r = Response(message=Message(), logs=[LogEntry.new("first")])
        r.add_log(LogEntry.new("second"))
        assert r.logs is not None
        assert len(r.logs) == 2


class TestResponseWorkflowList:
    def test_empty_when_none(self):
        assert Response(message=Message()).workflow_list == []

    def test_returns_list_when_set(self):
        op = workflow.OperationAnnotate(id="annotate")
        r = Response(message=Message(), workflow=[op])
        assert r.workflow_list == [op]


class TestResponseNew:
    def test_populates_versions_from_config(self):
        r = Response.new()
        assert r.schema_version == TRAPI_CONFIG.schema_version
        assert r.biolink_version == TRAPI_CONFIG.biolink_version
        assert isinstance(r.message, Message)
        assert r.logs is None
