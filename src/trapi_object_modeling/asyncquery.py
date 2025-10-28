from __future__ import annotations

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from trapi_object_modeling.query import Query


@dataclass(kw_only=True, config=ConfigDict(extra="allow"))
class AsyncQuery(Query):
    """The AsyncQuery class is effectively the same as the Query class but it requires a callback property."""

    callback: str
    """Upon completion, this server will send a POST request to the
            callback URL with `Content-Type: application/json` header and
            request body containing a JSON-encoded `Response` object.
            The server MAY POST `Response` objects before work is fully
            complete to provide interim results with a Response.status
            value of 'Running'. If a POST operation to the callback URL
            does not succeed, the server SHOULD retry the POST at least
            once.
    """
