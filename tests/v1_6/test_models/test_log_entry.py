"""Tests for translator_tom.v1_6.models.log_entry."""

import datetime

import pytest
from pydantic import ValidationError

from translator_tom.v1_6 import LogEntry, LogLevelEnum


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
        ts = datetime.datetime.now().astimezone().isoformat()
        e = LogEntry(timestamp=ts, message="hi")
        assert e.timestamp == ts
        assert e.message == "hi"
        assert e.level is None
        assert e.code is None

    def test_naive_timestamp_rejected(self):
        # Pattern requires a 'Z' or ±HH:MM timezone suffix; an offset-less ISO
        # string is rejected.
        with pytest.raises(ValidationError):
            LogEntry(timestamp=datetime.datetime.now().isoformat(), message="hi")

    def test_message_required(self):
        with pytest.raises(ValidationError):
            LogEntry(timestamp=datetime.datetime.now().astimezone().isoformat())  # type: ignore[call-arg]

    def test_timestamp_dt_round_trip(self):
        ts = datetime.datetime.now().astimezone()
        e = LogEntry(timestamp=ts.isoformat(), message="hi")
        assert e.timestamp_dt == ts

    def test_timestamp_dt_handles_z_suffix(self):
        e = LogEntry(timestamp="2020-09-03T18:13:49Z", message="hi")
        assert e.timestamp_dt == datetime.datetime(
            2020, 9, 3, 18, 13, 49, tzinfo=datetime.timezone.utc
        )


class TestLogEntryNew:
    def test_defaults(self):
        before = datetime.datetime.now().astimezone()
        e = LogEntry.new("hello")
        after = datetime.datetime.now().astimezone()
        assert e.message == "hello"
        assert e.level is None
        assert e.code is None
        # The timestamp falls within [before, after].
        assert before <= e.timestamp_dt <= after

    def test_with_level_and_code(self):
        e = LogEntry.new("oops", level="ERROR", code="QueryNotTraversable")
        assert e.message == "oops"
        assert e.level == "ERROR"
        assert e.code == "QueryNotTraversable"
