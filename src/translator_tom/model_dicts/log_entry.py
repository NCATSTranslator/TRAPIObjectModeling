from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from translator_tom.models.log_entry import LogLevel

__all__ = ["LogEntryDict"]


class LogEntryDict(TypedDict):
    timestamp: str
    level: NotRequired[LogLevel | None]
    code: NotRequired[str | None]
    message: str
