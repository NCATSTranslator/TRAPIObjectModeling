"""Transform for Response."""

from __future__ import annotations

from typing import Any

from translator_tom.v1_6.models.response import Response as V16Response
from translator_tom.v2_0._version import SCHEMA_VERSION
from translator_tom.v2_0.convert._message import _upgrade_message
from translator_tom.v2_0.convert._util import register
from translator_tom.v2_0.models.response import Response


@register(V16Response, Response)
def _upgrade_response(data: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Convert the message; drop empty logs; restamp a declared schema_version."""
    data = dict(data)

    data["message"] = _upgrade_message(data["message"], **kwargs)

    if not data.get("logs"):  # empty/absent logs array is invalid in 2.0
        data.pop("logs", None)
    if data.get("schema_version") is not None:
        data["schema_version"] = SCHEMA_VERSION

    return data
