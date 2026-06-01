from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from translator_tom.model_dicts.log_entry import LogEntryDict
from translator_tom.model_dicts.message import MessageDict
from translator_tom.model_dicts.workflow_operations import OperationDict

__all__ = ["ResponseDict"]


class ResponseDict(TypedDict):
    message: MessageDict
    status: NotRequired[str | None]
    description: NotRequired[str | None]
    logs: NotRequired[list[LogEntryDict]]
    workflow: NotRequired[list[OperationDict] | None]
    schema_version: NotRequired[str | None]
    biolink_version: NotRequired[str | None]
