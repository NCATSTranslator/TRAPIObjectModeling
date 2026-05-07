"""Tests for translator_tom.models.query."""

import pytest
from pydantic import ValidationError

from translator_tom import Message, Query, workflow


class TestQueryBasics:
    def test_required_field_only(self):
        q = Query(message=Message())
        assert isinstance(q.message, Message)
        assert q.log_level is None
        assert q.workflow is None
        assert q.submitter is None
        assert q.bypass_cache is False

    def test_message_required(self):
        with pytest.raises(ValidationError):
            Query()  # type: ignore[call-arg]

    def test_full_construction(self):
        q = Query(
            message=Message(),
            log_level="DEBUG",
            workflow=[workflow.OperationAnnotate(id="annotate")],
            submitter="me",
            bypass_cache=True,
        )
        assert q.log_level == "DEBUG"
        assert q.submitter == "me"
        assert q.bypass_cache is True


class TestQueryWorkflowList:
    def test_empty_when_none(self):
        assert Query(message=Message()).workflow_list == []

    def test_returns_list_when_set(self):
        op = workflow.OperationAnnotate(id="annotate")
        q = Query(message=Message(), workflow=[op])
        assert q.workflow_list == [op]


class TestQueryNew:
    def test_constructs_with_empty_message(self):
        q = Query.new()
        assert isinstance(q, Query)
        assert isinstance(q.message, Message)
