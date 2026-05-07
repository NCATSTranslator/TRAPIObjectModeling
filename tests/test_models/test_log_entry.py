"""Tests for translator_tom.models.log_entry."""

import datetime

import pytest
from pydantic import ValidationError

from translator_tom import LogEntry, LogLevelEnum


class TestLogLevelEnum:
    @pytest.mark.parametrize(
        ("member", "value"),
        [
            (LogLevelEnum.ERROR, "ERROR"),
            (LogLevelEnum.WARNING, "WARNING"),
            (LogLevelEnum.INFO, "INFO"),
            (LogLevelEnum.DEBUG, "DEBUG"),
        ],
    )
    def test_values(self, member: LogLevelEnum, value: str):
        assert member.value == value
        assert member == value


class TestLogEntryConstruction:
    def test_required_fields(self):
        ts = datetime.datetime.now().astimezone()
        e = LogEntry(timestamp=ts, message="hi")
        assert e.timestamp == ts
        assert e.message == "hi"
        assert e.level is None
        assert e.code is None

    def test_naive_timestamp_rejected(self):
        # AwareDatetime rejects timezone-naive datetimes.
        with pytest.raises(ValidationError):
            LogEntry(timestamp=datetime.datetime.now(), message="hi")

    def test_message_required(self):
        with pytest.raises(ValidationError):
            LogEntry(timestamp=datetime.datetime.now().astimezone())  # type: ignore[call-arg]


class TestLogEntryNew:
    def test_defaults(self):
        before = datetime.datetime.now().astimezone()
        e = LogEntry.new("hello")
        after = datetime.datetime.now().astimezone()
        assert e.message == "hello"
        assert e.level is None
        assert e.code is None
        # The timestamp falls within [before, after].
        assert before <= e.timestamp <= after

    def test_with_level_and_code(self):
        e = LogEntry.new("oops", level="ERROR", code="QueryNotTraversable")
        assert e.message == "oops"
        assert e.level == "ERROR"
        assert e.code == "QueryNotTraversable"
