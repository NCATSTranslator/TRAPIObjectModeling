"""Tests for `LogEntryDictUtil`, asserting parity with the `LogEntry` model."""

from __future__ import annotations

from translator_tom.model_dicts.log_entry import LogEntryDict, LogEntryDictUtil
from translator_tom.models.log_entry import LogEntry


class TestTimestampDt:
    def test_z_suffix_parity(self):
        entry: LogEntryDict = {"timestamp": "2020-09-03T18:13:49Z", "message": "hi"}
        model = LogEntry(timestamp="2020-09-03T18:13:49Z", message="hi")
        assert LogEntryDictUtil.timestamp_dt(entry) == model.timestamp_dt

    def test_offset_parity(self):
        entry: LogEntryDict = {
            "timestamp": "2020-09-03T18:13:49-04:00",
            "message": "hi",
        }
        model = LogEntry(timestamp="2020-09-03T18:13:49-04:00", message="hi")
        assert LogEntryDictUtil.timestamp_dt(entry) == model.timestamp_dt


class TestNew:
    def test_minimal_omits_none(self):
        entry = LogEntryDictUtil.new("a message")
        assert entry["message"] == "a message"
        assert "level" not in entry
        assert "code" not in entry
        # timestamp must be valid and round-trip through timestamp_dt
        assert LogEntryDictUtil.timestamp_dt(entry) is not None

    def test_with_level_and_code(self):
        entry = LogEntryDictUtil.new("msg", level="ERROR", code="KPNotAvailable")
        assert entry["level"] == "ERROR"
        assert entry["code"] == "KPNotAvailable"

    def test_matches_model_new_shape(self):
        entry = LogEntryDictUtil.new("msg", level="INFO")
        model_dict = LogEntry.new("msg", level="INFO").to_dict()
        # Same keys (timestamps differ by construction time).
        assert set(entry) == set(model_dict)
