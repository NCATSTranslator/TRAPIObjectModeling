"""Tests for translator_tom.models.auxiliary_graph.

In TRAPI 2.0 AuxiliaryGraph carries only `edges` (its `attributes` field was removed).
"""

import pytest
from pydantic import ValidationError

from translator_tom import AuxiliaryGraph


def _aux(edges: list[str] | None = None) -> AuxiliaryGraph:
    return AuxiliaryGraph(edges=edges or ["e1"])


class TestAuxiliaryGraphConstruction:
    def test_required_fields(self):
        a = _aux()
        assert a.edges == ["e1"]

    def test_edges_min_length_enforced(self):
        with pytest.raises(ValidationError):
            AuxiliaryGraph(edges=[])


class TestAuxiliaryGraphHash:
    def test_deterministic(self):
        a = _aux(["e1", "e2"])
        b = _aux(["e1", "e2"])
        assert a.hash() == b.hash()

    def test_edge_order_does_not_matter(self):
        a = _aux(["e1", "e2"])
        b = _aux(["e2", "e1"])
        assert a.hash() == b.hash()

    def test_changes_with_edges(self):
        a = _aux(["e1"])
        b = _aux(["e2"])
        assert a.hash() != b.hash()


class TestNormalize:
    def test_replaces_mapped_edges(self):
        a = _aux(["e1", "e2", "e3"])
        a.normalize({"e1": "E1", "e2": "E2"})
        assert a.edges == ["E1", "E2", "e3"]

    def test_unmapped_edges_unchanged(self):
        a = _aux(["e1"])
        a.normalize({"other": "OTHER"})
        assert a.edges == ["e1"]


class TestNormalizeAuxDict:
    def test_normalizes_all_graphs_in_dict(self):
        d = {"g1": _aux(["e1"]), "g2": _aux(["e2"])}
        AuxiliaryGraph.normalize_aux_dict(d, {"e1": "E1", "e2": "E2"})
        assert d["g1"].edges == ["E1"]
        assert d["g2"].edges == ["E2"]


class TestUpdate:
    def test_unions_edges(self):
        a = _aux(["e1", "e2"])
        b = _aux(["e2", "e3"])
        a.update(b)
        assert set(a.edges) == {"e1", "e2", "e3"}


class TestMergeDictionaries:
    def test_adds_new_keys(self):
        old = {"g1": _aux(["e1"])}
        new = {"g2": _aux(["e2"])}
        AuxiliaryGraph.merge_dictionaries(old, new)
        assert set(old) == {"g1", "g2"}

    def test_updates_existing_keys(self):
        old = {"g1": _aux(["e1"])}
        new = {"g1": _aux(["e2"])}
        AuxiliaryGraph.merge_dictionaries(old, new)
        assert set(old["g1"].edges) == {"e1", "e2"}
