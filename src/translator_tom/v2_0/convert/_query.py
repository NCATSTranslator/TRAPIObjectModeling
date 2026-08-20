"""Converter for Query (also covers AsyncQuery via MRO)."""

from __future__ import annotations

from typing import Any

from translator_tom.v1_6.models.query import Query as V16Query
from translator_tom.v2_0.convert._util import _build, _v2_equivalent, up_version


@up_version.register(V16Query)
def _convert_query(obj: V16Query, **kwargs: Any) -> Any:
    """Move log_level/bypass_cache under `parameters`; convert the message.

    Dispatches for AsyncQuery too (a Query subclass); `_v2_equivalent` preserves the
    concrete type so a converted AsyncQuery keeps its `callback`.
    """
    target = _v2_equivalent(type(obj))
    data = obj.to_dict()

    log_level = data.pop("log_level", None)
    bypass_cache = data.pop("bypass_cache", None)
    parameters: dict[str, Any] = {}

    if log_level is not None:
        parameters["log_level"] = log_level
    if bypass_cache:  # only a non-default True survives to_dict
        parameters["bypass_cache"] = bypass_cache
    if parameters:
        data["parameters"] = parameters

    data["message"] = up_version(obj.message, **kwargs).to_dict()

    return _build(target, data)
