from __future__ import annotations

import datetime
from enum import Enum
from typing import Annotated, Literal

from pydantic import Field
from typing_extensions import Self

from translator_tom.utils.object_base import TOMBase

# Matches the AwareDatetime-accepted subset of ISO 8601 / RFC 3339: date + 'T' +
# time, optional fractional seconds, required 'Z' or ±HH(:)MM timezone.
_ISO_8601_AWARE_PATTERN = (
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})$"
)

__all__ = [
    "LogEntry",
    "LogLevel",
    "LogLevelEnum",
]


class LogLevelEnum(str, Enum):
    """Standardized log levels."""

    ERROR = "ERROR"
    """The log presents an error which may affect response integrity."""

    WARNING = "WARNING"
    """The log presents some state which may affect response quality."""

    INFO = "INFO"
    """The log presents information about query execution that may be useful to users."""

    DEBUG = "DEBUG"
    """The log presents information about query execution that may be useful to devs."""


LogLevel = Literal["ERROR", "WARNING", "INFO", "DEBUG"]


class LogEntry(TOMBase):
    """The LogEntry object contains information useful for tracing and debugging across Translator components.

    Although an individual component (for example, an ARA or KP) may have its
    own logging and debugging infrastructure, this internal
    information is not, in general, available to other components.
    In addition to a timestamp and logging level, LogEntry
    includes a string intended to be read by a human, along with
    one of a standardized set of codes describing the condition of
    the component sending the message.
    """

    timestamp: Annotated[str, Field(pattern=_ISO_8601_AWARE_PATTERN)]
    """Timestamp in ISO 8601 format, providing the LogEntry time

    either in univeral coordinated time (UTC) using the 'Z' tag
    (e.g 2020-09-03T18:13:49Z), or, if local time is provided,
    the timezone offset must be provided
    (e.g. 2020-09-03T18:13:49-04:00).
    """

    level: LogLevel | None = None

    code: str | None = None
    """One of a standardized set of short codes e.g. QueryNotTraversable, KPNotAvailable, KPResponseMalformed."""

    message: str
    """A human-readable log message."""

    @property
    def timestamp_dt(self) -> datetime.datetime:
        """Return the timestamp parsed as a timezone-aware `datetime`."""
        # datetime.fromisoformat() only accepts 'Z' as of Python 3.11; normalize for 3.10.
        ts = self.timestamp
        if ts.endswith("Z"):
            ts = f"{ts[:-1]}+00:00"
        return datetime.datetime.fromisoformat(ts)

    @classmethod
    def new(
        cls, message: str, level: LogLevel | None = None, code: str | None = None
    ) -> Self:
        """Return a new LogEntry with a timestamp from now."""
        return cls.model_construct(
            timestamp=datetime.datetime.now().astimezone().isoformat(),
            level=level,
            code=code,
            message=message,
        )
