from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from translator_tom.utils.dict_util_base import DictUtil
from translator_tom.v2_0.model_dicts.message import MessageDict
from translator_tom.v2_0.model_dicts.query_parameters import QueryParametersDict
from translator_tom.v2_0.model_dicts.workflow_operations import OperationDict
from translator_tom.v2_0.models.query import Query

__all__ = ["QueryDict", "QueryDictUtil"]


class QueryDict(TypedDict):
    submitter: NotRequired[str | None]
    parameters: NotRequired[QueryParametersDict | None]
    message: MessageDict
    workflow: NotRequired[list[OperationDict] | None]


class QueryDictUtil(DictUtil[QueryDict]):
    """Utility methods for `QueryDict`, mirroring those on the `Query` model."""

    _model = Query

    @staticmethod
    def workflow_list(query: QueryDict) -> list[OperationDict]:
        """Get the workflow operations as a guaranteed list, even if they are represented as None."""
        workflow = query.get("workflow")
        return workflow if workflow is not None else []

    @staticmethod
    def get_parameters(query: QueryDict) -> QueryParametersDict:
        """Get the parameters, or an empty QueryParametersDict if they are represented as None."""
        parameters = query.get("parameters")
        return parameters if parameters is not None else {}

    @staticmethod
    def new() -> QueryDict:
        """Return an empty instance, without having to pass required containers."""
        return {"message": {}}
