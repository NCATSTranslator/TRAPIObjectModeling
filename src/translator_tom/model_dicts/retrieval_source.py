from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from translator_tom.models.retrieval_source import ResourceRole
from translator_tom.models.shared import Infores

__all__ = ["RetrievalSourceDict"]


class RetrievalSourceDict(TypedDict):
    resource_id: Infores
    resource_role: ResourceRole
    upstream_resource_ids: NotRequired[list[Infores] | None]
    source_record_urls: NotRequired[list[str] | None]
