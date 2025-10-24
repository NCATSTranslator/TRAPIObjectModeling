from __future__ import annotations

import datetime

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from trapi_object_modeling.log_level import LogLevel


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
class LogEntry:
    """The LogEntry object contains information useful for tracing and debugging across Translator components.

    Although an individual component (for example, an ARA or KP) may have its
    own logging and debugging infrastructure, this internal
    information is not, in general, available to other components.
    In addition to a timestamp and logging level, LogEntry
    includes a string intended to be read by a human, along with
    one of a standardized set of codes describing the condition of
    the component sending the message.
    """

    timestamp: datetime.datetime
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
