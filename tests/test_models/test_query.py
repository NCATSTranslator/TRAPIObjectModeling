"""Tests for translator_tom.models.query."""

import pytest
from pydantic import ValidationError

from translator_tom import Message, Query, QueryParameters, workflow


class TestQueryBasics:
    def test_required_field_only(self):
        q = Query(message=Message())
        assert isinstance(q.message, Message)
        assert q.parameters is None
        assert q.workflow is None
        assert q.submitter is None

    def test_message_required(self):
        with pytest.raises(ValidationError):
            Query()  # type: ignore[call-arg]

    def test_full_construction(self):
        q = Query(
            message=Message(),
            parameters=QueryParameters(log_level="DEBUG", bypass_cache=True),
            workflow=[workflow.OperationAnnotate(id="annotate")],
            submitter="me",
        )
        assert q.parameters is not None
        assert q.parameters.log_level == "DEBUG"
        assert q.parameters.bypass_cache is True
        assert q.submitter == "me"


class TestQueryGetParameters:
    def test_returns_empty_when_none(self):
        params = Query(message=Message()).get_parameters()
        assert isinstance(params, QueryParameters)
        assert params.log_level is None
        assert params.timeout is None
        assert params.bypass_cache is False

    def test_returns_parameters_when_set(self):
        params = QueryParameters(timeout=5.0)
        q = Query(message=Message(), parameters=params)
        assert q.get_parameters() is params


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
