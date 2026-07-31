from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from translator_tom.model_dicts.log_entry import LogEntryDict
from translator_tom.model_dicts.message import MessageDict
from translator_tom.model_dicts.workflow_operations import OperationDict
from translator_tom.models.response import Response
from translator_tom.utils.config import TRAPI_CONFIG
from translator_tom.utils.dict_util_base import DictUtil

__all__ = ["ResponseDict", "ResponseDictUtil"]


class ResponseDict(TypedDict):
    message: MessageDict
    status: NotRequired[str | None]
    description: NotRequired[str | None]
    logs: NotRequired[list[LogEntryDict]]
    workflow: NotRequired[list[OperationDict] | None]
    schema_version: NotRequired[str | None]
    biolink_version: NotRequired[str | None]


class ResponseDictUtil(DictUtil[ResponseDict]):
    """Utility methods for `ResponseDict`, mirroring those on the `Response` model."""

    _model = Response

    @staticmethod
    def workflow_list(response: ResponseDict) -> list[OperationDict]:
        """Get the workflow operations as a guaranteed list, even if they are represented as None."""
        workflow = response.get("workflow")
        return workflow if workflow is not None else []

    @staticmethod
    def new() -> ResponseDict:
        """Return an empty instance, without having to pass required containers."""
        # logs defaults to [] and is dropped by exclude_defaults, matching Response.new().
        return {
            "message": {},
            "schema_version": TRAPI_CONFIG.schema_version,
            "biolink_version": TRAPI_CONFIG.biolink_version,
        }
