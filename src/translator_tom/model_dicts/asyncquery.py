from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from translator_tom.model_dicts.log_entry import LogEntryDict
from translator_tom.model_dicts.query import QueryDict

__all__ = [
    "AsyncQueryDict",
    "AsyncQueryResponseDict",
    "AsyncQueryStatusResponseDict",
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
