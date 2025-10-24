from __future__ import annotations

from enum import Enum


# TODO: check these log level definitions with TOM
class LogLevel(str, Enum):
    """Standardized log levels."""

    ERROR = "ERROR"
    """The log presents an error which may affect response integrity."""

    WARNING = "WARNING"
    """The log presents some state which may affect response quality."""

    INFO = "INFO"
    """The log presents information about query execution that may be useful to users."""

    DEBUG = "DEBUG"
    """The log presents information about query execution that may be useful to devs."""
