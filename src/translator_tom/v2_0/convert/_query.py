"""Transform for Query (and AsyncQuery)."""

from __future__ import annotations

from typing import Any

from translator_tom.v1_6.models.asyncquery import AsyncQuery as V16AsyncQuery
from translator_tom.v1_6.models.query import Query as V16Query
from translator_tom.v2_0.convert._message import _upgrade_message
from translator_tom.v2_0.convert._util import register
from translator_tom.v2_0.models.asyncquery import AsyncQuery
from translator_tom.v2_0.models.query import Query


@register(V16Query, Query)
@register(V16AsyncQuery, AsyncQuery)
def _upgrade_query(data: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Move log_level/bypass_cache under `parameters`; convert the message.

    Registered for AsyncQuery too (same transform); its target keeps the `callback`,
    which rides through `data` untouched.
    """
    data = dict(data)

    log_level = data.pop("log_level", None)
    bypass_cache = data.pop("bypass_cache", None)
    parameters: dict[str, Any] = {}
    if log_level is not None:
        parameters["log_level"] = log_level
    if bypass_cache:  # only a non-default True survives to_dict
        parameters["bypass_cache"] = bypass_cache
    if parameters:
        data["parameters"] = parameters

    data["message"] = _upgrade_message(data["message"], **kwargs)

    return data
