from __future__ import annotations

from typing import overload

from translator_tom.utils.object_base import TOMBase
from translator_tom.v2_0.models.log_entry import LogLevel

__all__ = ["QueryParameters"]


class QueryParameters(TOMBase):
    """Query-time parameters that don't affect the semantics of a query or intended workflow, but may affect overall behavior of the server in the execution of this query.

    The server MUST repeat the parameters it is given in its Response.
    """

    timeout: float | None = None
    """Custom time in seconds that the client is willing to wait for a response.

    After this time has elapsed, the service MAY consider the query
    failed and respond with logs indicating as such.
    If the service knows it cannot respond in the given time, it MAY
    respond with an HTTP 409 and a response explaining its time capabilities.
    Negative values SHOULD be interpreted as disabling any default
    timeout the server implements.
    """

    log_level: LogLevel | None = None
    """The least critical level of logs to return."""

    bypass_cache: bool = False
    """Set to true in order to request that the agent obtain
    fresh information from its sources in all cases where
    it has a viable choice between requesting fresh information
    in real time and using cached information.

    The agent receiving this flag MUST also include it in TRAPI sent to
    downstream sources (e.g., ARS -> ARAs -> KPs).
    """

    @overload
    def get_timeout(self) -> float | None: ...
    @overload
    def get_timeout(self, default: float) -> float: ...
    def get_timeout(self, default: float | None = None) -> float | None:
        """Get `timeout`, or `default` if it is absent."""
        return self.timeout if self.timeout is not None else default

    @overload
    def get_log_level(self) -> LogLevel | None: ...
    @overload
    def get_log_level(self, default: LogLevel) -> LogLevel: ...
    def get_log_level(self, default: LogLevel | None = None) -> LogLevel | None:
        """Get `log_level`, or `default` if it is absent."""
        return self.log_level if self.log_level is not None else default
