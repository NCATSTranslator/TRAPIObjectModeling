from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from translator_tom.model_dicts.message import MessageDict
from translator_tom.model_dicts.workflow_operations import OperationDict
from translator_tom.models.log_entry import LogLevel
from translator_tom.models.query import Query
from translator_tom.utils.dict_util_base import DictUtil

__all__ = ["QueryDict", "QueryDictUtil"]


class QueryDict(TypedDict):
    message: MessageDict
    log_level: NotRequired[LogLevel | None]
    workflow: NotRequired[list[OperationDict] | None]
    submitter: NotRequired[str | None]
    bypass_cache: NotRequired[bool]


class QueryDictUtil(DictUtil[QueryDict]):
    """Utility methods for `QueryDict`, mirroring those on the `Query` model."""

    _model = Query

    @staticmethod
    def workflow_list(query: QueryDict) -> list[OperationDict]:
        """Get the workflow operations as a guaranteed list, even if they are represented as None."""
        workflow = query.get("workflow")
        return workflow if workflow is not None else []

    @staticmethod
    def new() -> QueryDict:
        """Return an empty instance, without having to pass required containers."""
        return {"message": {}}
