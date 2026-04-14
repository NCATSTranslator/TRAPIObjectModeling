from __future__ import annotations

from enum import Enum
from typing import Literal

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


class Curie:
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


Infores = str
"""A CURIE which begins with `infores:`"""


def infores(ref: str) -> Infores:
    """Return a properly-formed infores."""
    return f"infores:{ref.removeprefix('infores:')}"


BiolinkPredicate = str
"""CURIE for a Biolink 'predicate' slot, taken from the Biolink slot ('is_a') hierarchy rooted in biolink:related_to (snake_case).
This predicate defines the Biolink relationship between the subject and
object nodes of a biolink:Association defining a knowledge graph edge.
"""

BiolinkEntity = str
"""Compact URI (CURIE) for a Biolink class, biolink:NamedThing or a child thereof.
The CURIE must use the prefix 'biolink:'
followed by the PascalCase class name.
"""


def biolink(ref: str) -> BiolinkPredicate | BiolinkEntity:
    """Return a properly-formed biolink element."""
    return f"biolink:{ref.removeprefix('biolink:')}"


##### Enums


class KnowledgeTypeEnum(str, Enum):
    """Edge knowledge types that are supported for querying."""

    lookup = "lookup"
    """Knowledge that is directly available."""

    inferred = "inferred"
    """Knowledge that is autonomously speculated by the reasoner through various means."""


KnowledgeType = Literal["lookup", "inferred"]
