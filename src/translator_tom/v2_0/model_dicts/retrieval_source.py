from __future__ import annotations

from typing_extensions import NotRequired, TypedDict

from translator_tom.utils.dict_util_base import DictUtil
from translator_tom.utils.hash import tomhash
from translator_tom.utils.shared import Infores
from translator_tom.v2_0.models.retrieval_source import ResourceRole, RetrievalSource

__all__ = ["RetrievalSourceDict", "RetrievalSourceDictUtil"]


class RetrievalSourceDict(TypedDict):
    resource_id: Infores
    resource_role: ResourceRole
    upstream_resource_ids: NotRequired[list[Infores] | None]
    source_record_urls: NotRequired[list[str] | None]


class RetrievalSourceDictUtil(DictUtil[RetrievalSourceDict]):
    """Utility methods for `RetrievalSourceDict`, mirroring those on the `RetrievalSource` model."""

    _model = RetrievalSource

    @staticmethod
    def upstream_resource_ids_list(source: RetrievalSourceDict) -> list[Infores]:
        """Get the upstream resource IDs as a guaranteed list, even if they are represented as None."""
        upstream_resource_ids = source.get("upstream_resource_ids")
        return upstream_resource_ids if upstream_resource_ids is not None else []

    @staticmethod
    def source_record_urls_list(source: RetrievalSourceDict) -> list[str]:
        """Get the source record URLs as a guaranteed list, even if they are represented as None."""
        source_record_urls = source.get("source_record_urls")
        return source_record_urls if source_record_urls is not None else []

    @classmethod
    def hash(cls, obj: RetrievalSourceDict) -> str:
        """Hash matching `RetrievalSource.hash` (resource identity and role only)."""
        return tomhash((obj["resource_id"], obj["resource_role"]))

    @staticmethod
    def update(source: RetrievalSourceDict, other: RetrievalSourceDict) -> None:
        """Update the first source in-place, merging information from the second."""
        other_upstream = other.get("upstream_resource_ids")
        if other_upstream:
            source["upstream_resource_ids"] = list(
                set(source.get("upstream_resource_ids") or []) | set(other_upstream)
            )
