from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Annotated, Any, Literal, override

from pydantic import JsonValue
from pydantic_core import core_schema

##### Internal IDs with no set structure

QNodeID = str
QEdgeID = str
QPathID = str
EdgeID = str
AuxGraphID = str

##### CURIEs, etc.

CURIE = str
"""A Compact URI, consisting of a prefix and a reference separated by a colon, such as UniProtKB:P00738.
Via an external context definition, the CURIE prefix and colon may be replaced by a URI
prefix, such as http://identifiers.org/uniprot/, to form a full URI.
"""

Infores = CURIE
"""A CURIE which begins with `infores:`"""


def infores(ref: str) -> Infores:
    """Return a properly-formed infores."""
    return f"infores:{ref.removeprefix('infores:')}"


class _CurieMeta(type):
    """Metaclass that allows for calling Curie."""

    @override
    def __call__(cls, prefix: str, reference: str) -> CURIE:
        """Return a CURIE."""
        return f"{prefix}:{reference}"


class Curie(metaclass=_CurieMeta):
    """A holding class for CURIE utility methods."""

    @staticmethod
    def split(curie: CURIE) -> tuple[str, str]:
        """Split a curie into prefix and reference."""
        parts = curie.split(":", maxsplit=1)
        if len(parts) == 1:
            return "", parts[0]
        return parts[0], parts[1]

    @staticmethod
    def get_prefix(curie: CURIE) -> str:
        """Get the prefix of a CURIE."""
        return Curie.split(curie)[0]

    @staticmethod
    def get_reference(curie: CURIE) -> str:
        """Get the reference of a CURIE."""
        return Curie.split(curie)[1]

    @staticmethod
    def ensure_prefix(prefix: str, curie: CURIE) -> str:
        """Ensure the only prefix the CURIE has is the given one."""
        return f"{prefix}:{Curie.get_reference(curie)}"

    rmprefix: Callable[[CURIE], str] = staticmethod(get_reference)
    rmref: Callable[[CURIE], str] = staticmethod(get_prefix)


##### Enums


class KnowledgeTypeEnum(str, Enum):
    """Edge knowledge types that are supported for querying."""

    lookup = "lookup"
    """Knowledge that is directly available."""

    inferred = "inferred"
    """Knowledge that is autonomously speculated by the reasoner through various means."""


KnowledgeType = Literal["lookup", "inferred"]


##### Custom annotations


class _AnyCoreSchema:
    """Pydantic annotation that installs `any_schema` for both validate and dump.

    Skips python calls when serializing to reduce overhead.
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Any, handler: Any
    ) -> core_schema.CoreSchema:
        return core_schema.any_schema()


FastJsonValue = Annotated[JsonValue, _AnyCoreSchema()]
"""`JsonValue` for type-checking, but validate/dump like Any to skip overhead."""
