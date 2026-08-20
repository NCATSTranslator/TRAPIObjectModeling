from __future__ import annotations

from typing import overload

from typing_extensions import NotRequired, TypedDict

from translator_tom.utils.dict_util_base import DictUtil
from translator_tom.v2_0.models.log_entry import LogLevel
from translator_tom.v2_0.models.query_parameters import QueryParameters

__all__ = ["QueryParametersDict", "QueryParametersDictUtil"]


class QueryParametersDict(TypedDict):
    timeout: NotRequired[float | None]
    log_level: NotRequired[LogLevel | None]
    bypass_cache: NotRequired[bool]


class QueryParametersDictUtil(DictUtil[QueryParametersDict]):
    """Utility methods for `QueryParametersDict`, mirroring those on the `QueryParameters` model."""

    _model = QueryParameters

    @overload
    @staticmethod
    def get_timeout(params: QueryParametersDict) -> float | None: ...
    @overload
    @staticmethod
    def get_timeout(params: QueryParametersDict, default: float) -> float: ...
    @staticmethod
    def get_timeout(
        params: QueryParametersDict, default: float | None = None
    ) -> float | None:
        """Get `timeout`, or `default` if it is absent."""
        timeout = params.get("timeout")
        return timeout if timeout is not None else default

    @overload
    @staticmethod
    def get_log_level(params: QueryParametersDict) -> LogLevel | None: ...
    @overload
    @staticmethod
    def get_log_level(params: QueryParametersDict, default: LogLevel) -> LogLevel: ...
    @staticmethod
    def get_log_level(
        params: QueryParametersDict, default: LogLevel | None = None
    ) -> LogLevel | None:
        """Get `log_level`, or `default` if it is absent."""
        log_level = params.get("log_level")
        return log_level if log_level is not None else default
