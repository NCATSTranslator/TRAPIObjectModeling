from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from translator_tom.model_dicts.message import MessageDict
from translator_tom.model_dicts.workflow_operations import OperationDict
from translator_tom.models.log_entry import LogLevel

__all__ = ["QueryDict"]


class QueryDict(TypedDict):
    message: MessageDict
    log_level: NotRequired[LogLevel | None]
    workflow: NotRequired[list[OperationDict] | None]
    submitter: NotRequired[str | None]
    bypass_cache: NotRequired[bool]
