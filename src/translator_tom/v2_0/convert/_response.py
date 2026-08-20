"""Converter for Response."""

from __future__ import annotations

from typing import Any

from translator_tom.v1_6.models.response import Response as V16Response
from translator_tom.v2_0._version import SCHEMA_VERSION
from translator_tom.v2_0.convert._util import _build, up_version
from translator_tom.v2_0.models.response import Response


@up_version.register(V16Response)
def _convert_response(obj: V16Response, **kwargs: Any) -> Response:
    """Convert the message; drop empty logs; restamp a declared schema_version."""
    data = obj.to_dict()

    data["message"] = up_version(obj.message, **kwargs).to_dict()

    if not obj.logs:  # empty/absent logs array is invalid in 2.0
        data.pop("logs", None)
    if obj.schema_version is not None:
        data["schema_version"] = SCHEMA_VERSION

    return _build(Response, data)
