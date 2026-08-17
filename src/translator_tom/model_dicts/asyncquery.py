from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from translator_tom.model_dicts.log_entry import LogEntryDict

# MessageDict/LogLevel are in scope so pydantic can resolve QueryDict's inherited
# forward-ref fields when building TypeAdapter[AsyncQueryDict] (validate=True).
from translator_tom.model_dicts.message import MessageDict  # noqa: F401
from translator_tom.model_dicts.query import QueryDict
from translator_tom.model_dicts.workflow_operations import OperationDict
from translator_tom.models.asyncquery import (
    AsyncQuery,
    AsyncQueryResponse,
    AsyncQueryStatusResponse,
)
from translator_tom.models.log_entry import LogLevel  # noqa: F401
from translator_tom.utils.dict_util_base import DictUtil

__all__ = [
    "AsyncQueryDict",
    "AsyncQueryDictUtil",
    "AsyncQueryResponseDict",
    "AsyncQueryResponseDictUtil",
    "AsyncQueryStatusResponseDict",
    "AsyncQueryStatusResponseDictUtil",
]


class AsyncQueryDict(QueryDict):
    callback: str


class AsyncQueryResponseDict(TypedDict):
    status: NotRequired[str | None]
    description: NotRequired[str | None]
    job_id: str


class AsyncQueryStatusResponseDict(TypedDict):
    status: str
    description: str
    logs: list[LogEntryDict]
    response_url: NotRequired[str | None]


class AsyncQueryDictUtil(DictUtil[AsyncQueryDict]):
    """Utility methods for `AsyncQueryDict`, mirroring those on the `AsyncQuery` model."""

    _model = AsyncQuery

    @staticmethod
    def workflow_list(query: AsyncQueryDict) -> list[OperationDict]:
        """Get the workflow operations as a guaranteed list, even if they are represented as None."""
        workflow = query.get("workflow")
        return workflow if workflow is not None else []

    @staticmethod
    def new(callback: str) -> AsyncQueryDict:
        """Return an empty instance, without having to pass required containers."""
        return {"message": {}, "callback": callback}


class AsyncQueryResponseDictUtil(DictUtil[AsyncQueryResponseDict]):
    """Utility methods for `AsyncQueryResponseDict`, mirroring the `AsyncQueryResponse` model."""

    _model = AsyncQueryResponse


class AsyncQueryStatusResponseDictUtil(DictUtil[AsyncQueryStatusResponseDict]):
    """Utility methods for `AsyncQueryStatusResponseDict`, mirroring the `AsyncQueryStatusResponse` model."""

    _model = AsyncQueryStatusResponse
