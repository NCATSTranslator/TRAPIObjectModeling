"""Tests for translator_tom.models.response."""

import pytest
from pydantic import ValidationError

from translator_tom import Message, Response, workflow
from translator_tom.utils.config import TRAPI_CONFIG


class TestResponseBasics:
    def test_required_field(self):
        r = Response(message=Message())
        assert isinstance(r.message, Message)
        assert r.status is None
        assert r.description is None
        assert r.logs is None
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
