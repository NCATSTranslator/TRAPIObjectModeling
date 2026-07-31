from __future__ import annotations

import datetime

from typing_extensions import NotRequired, TypedDict

from translator_tom.models.log_entry import LogEntry, LogLevel
from translator_tom.utils.dict_util_base import DictUtil

__all__ = ["LogEntryDict", "LogEntryDictUtil"]


class LogEntryDict(TypedDict):
    timestamp: str
    level: NotRequired[LogLevel | None]
    code: NotRequired[str | None]
    message: str


class LogEntryDictUtil(DictUtil[LogEntryDict]):
    """Utility methods for `LogEntryDict`, mirroring those on the `LogEntry` model."""

    _model = LogEntry

    @staticmethod
    def timestamp_dt(log_entry: LogEntryDict) -> datetime.datetime:
        """Return the timestamp parsed as a timezone-aware `datetime`."""
        # datetime.fromisoformat() only accepts 'Z' as of Python 3.11; normalize for 3.10.
        ts = log_entry["timestamp"]
        if ts.endswith("Z"):
            ts = f"{ts[:-1]}+00:00"
        return datetime.datetime.fromisoformat(ts)

    @staticmethod
    def new(
        message: str, level: LogLevel | None = None, code: str | None = None
    ) -> LogEntryDict:
        """Return a new LogEntry dict with a timestamp from now."""
        log_entry: LogEntryDict = {
            "timestamp": datetime.datetime.now().astimezone().isoformat(),
            "message": message,
        }
        if level is not None:
            log_entry["level"] = level
        if code is not None:
            log_entry["code"] = code
        return log_entry
