from __future__ import annotations

from enum import Enum

QNodeID = str
QEdgeID = str
QPathID = str

CURIE = str
"""A Compact URI, consisting of a prefix and a reference separated by a colon, such as UniProtKB:P00738.
Via an external context definition, the CURIE prefix and colon may be replaced by a URI
prefix, such as http://identifiers.org/uniprot/, to form a full URI.
"""

EdgeID = str
AuxGraphID = str

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


class KnowledgeTypeEnum(str, Enum):
    """Edge knowledge types that are supported for querying."""

    lookup = "lookup"
    """Knowledge that is directly available."""

    inferred = "inferred"
    """Knowledge that is autonomously speculated by the reasoner through various means."""
