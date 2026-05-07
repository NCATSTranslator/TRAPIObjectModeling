"""Tests for translator_tom.models.auxiliary_graph."""

import pytest
from pydantic import ValidationError

from translator_tom import Attribute, AuxiliaryGraph


def _attr(value: int = 1, type_id: str = "biolink:foo") -> Attribute:
    return Attribute(attribute_type_id=type_id, value=value)


def _aux(edges: list[str] | None = None, attrs: list[Attribute] | None = None) -> AuxiliaryGraph:
    return AuxiliaryGraph(edges=edges or ["e1"], attributes=attrs or [])


class TestAuxiliaryGraphConstruction:
    def test_required_fields(self):
        a = _aux()
        assert a.edges == ["e1"]
        assert a.attributes == []

    def test_edges_min_length_enforced(self):
        with pytest.raises(ValidationError):
            AuxiliaryGraph(edges=[], attributes=[])


class TestAuxiliaryGraphHash:
    def test_deterministic(self):
        a = _aux(["e1", "e2"])
        b = _aux(["e1", "e2"])
        assert a.hash() == b.hash()

    def test_edge_order_does_not_matter(self):
        a = _aux(["e1", "e2"])
        b = _aux(["e2", "e1"])
        assert a.hash() == b.hash()

    def test_changes_with_attributes(self):
        a = _aux(attrs=[_attr(1)])
        b = _aux(attrs=[_attr(2)])
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
    def test_assigns_attributes_when_self_empty(self):
        a = _aux(attrs=[])
        b = _aux(attrs=[_attr(1)])
        a.update(b)
        assert len(a.attributes) == 1

    def test_merges_attributes_when_both_present(self):
        a = _aux(attrs=[_attr(1, "biolink:a")])
        b = _aux(attrs=[_attr(2, "biolink:b")])
        a.update(b)
        assert len(a.attributes) == 2

    def test_does_not_overwrite_when_other_empty(self):
        a = _aux(attrs=[_attr(1)])
        b = _aux(attrs=[])
        a.update(b)
        assert len(a.attributes) == 1


class TestMergeDictionaries:
    def test_adds_new_keys(self):
        old = {"g1": _aux(["e1"])}
        new = {"g2": _aux(["e2"])}
        AuxiliaryGraph.merge_dictionaries(old, new)
        assert set(old) == {"g1", "g2"}

    def test_updates_existing_keys(self):
        old = {"g1": _aux(["e1"], [_attr(1, "biolink:a")])}
        new = {"g1": _aux(["e1"], [_attr(2, "biolink:b")])}
        AuxiliaryGraph.merge_dictionaries(old, new)
        assert len(old["g1"].attributes) == 2
