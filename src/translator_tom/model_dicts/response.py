from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from translator_tom.model_dicts.log_entry import LogEntryDict
from translator_tom.model_dicts.message import MessageDict
from translator_tom.model_dicts.query_parameters import QueryParametersDict
from translator_tom.model_dicts.workflow_operations import OperationDict
from translator_tom.models.response import Response
from translator_tom.utils.config import TRAPI_CONFIG
from translator_tom.utils.dict_util_base import DictUtil

__all__ = ["ResponseDict", "ResponseDictUtil"]


class ResponseDict(TypedDict):
    parameters: NotRequired[QueryParametersDict | None]
    message: MessageDict
    status: NotRequired[str | None]
    description: NotRequired[str | None]
    logs: NotRequired[list[LogEntryDict] | None]
    workflow: NotRequired[list[OperationDict] | None]
    schema_version: NotRequired[str | None]
    biolink_version: NotRequired[str | None]
    data_release_versions: NotRequired[dict[str, str] | None]


class ResponseDictUtil(DictUtil[ResponseDict]):
    """Utility methods for `ResponseDict`, mirroring those on the `Response` model."""

    _model = Response

    @staticmethod
    def workflow_list(response: ResponseDict) -> list[OperationDict]:
        """Get the workflow operations as a guaranteed list, even if they are represented as None."""
        workflow = response.get("workflow")
        return workflow if workflow is not None else []

    @staticmethod
    def logs_list(response: ResponseDict) -> list[LogEntryDict]:
        """Get the logs as a guaranteed list, even if they are represented as None."""
        logs = response.get("logs")
        return logs if logs is not None else []

    @staticmethod
    def data_release_versions_dict(response: ResponseDict) -> dict[str, str]:
        """Get the data_release_versions as a guaranteed dict, even if they are represented as None."""
        data_release_versions = response.get("data_release_versions")
        return data_release_versions if data_release_versions is not None else {}

    @staticmethod
    def add_log(response: ResponseDict, entry: LogEntryDict) -> None:
        """Append a LogEntry, initializing the logs list if it is absent."""
        logs = response.get("logs")
        if logs is None:
            response["logs"] = [entry]
        else:
            logs.append(entry)

    @staticmethod
    def new() -> ResponseDict:
        """Return an empty instance, without having to pass required containers."""
        # logs is omitted (optional, absent when empty), matching Response.new().
        return {
            "message": {},
            "schema_version": TRAPI_CONFIG.schema_version,
            "biolink_version": TRAPI_CONFIG.biolink_version,
        }
