"""Tests for `AuxiliaryGraphDictUtil`, asserting parity with the model."""

from __future__ import annotations

from translator_tom.v1_6.model_dicts.auxiliary_graph import (
    AuxiliaryGraphDict,
    AuxiliaryGraphDictUtil,
)
from translator_tom.v1_6.models.attribute import Attribute
from translator_tom.v1_6.models.auxiliary_graph import AuxiliaryGraph


def _aux(*edges: str, attrs: list[Attribute] | None = None) -> AuxiliaryGraph:
    return AuxiliaryGraph(edges=list(edges), attributes=attrs or [])


class TestHashParity:
    def test_no_attributes(self):
        a = _aux("e0", "e1")
        assert AuxiliaryGraphDictUtil.hash(a.to_dict()) == a.hash()

    def test_with_attributes(self):
        a = _aux("e0", attrs=[Attribute(attribute_type_id="biolink:x", value=1)])
        assert AuxiliaryGraphDictUtil.hash(a.to_dict()) == a.hash()

    def test_edges_unordered(self):
        a = _aux("e0", "e1")
        b = _aux("e1", "e0")
        assert AuxiliaryGraphDictUtil.hash(a.to_dict()) == AuxiliaryGraphDictUtil.hash(
            b.to_dict()
        )


class TestNormalize:
    def test_parity(self):
        model = _aux("e0", "e1", "e2")
        aux_dict = model.to_dict()
        mapping = {"e0": "n0", "e2": "n2"}
        model.normalize(mapping)
        AuxiliaryGraphDictUtil.normalize(aux_dict, mapping)
        assert aux_dict["edges"] == model.edges

    def test_normalize_aux_dict_parity(self):
        model_map = {"a0": _aux("e0"), "a1": _aux("e1")}
        dict_map: dict[str, AuxiliaryGraphDict] = {
            k: v.to_dict() for k, v in model_map.items()
        }
        mapping = {"e0": "n0"}
        for v in model_map.values():
            v.normalize(mapping)
        AuxiliaryGraphDictUtil.normalize_aux_dict(dict_map, mapping)
        assert dict_map == {k: v.to_dict() for k, v in model_map.items()}


class TestUpdate:
    def test_takes_other_attributes_when_empty(self):
        model = _aux("e0")
        other = _aux("e0", attrs=[Attribute(attribute_type_id="biolink:x", value=1)])
        aux_dict = model.to_dict()
        model.update(other)
        AuxiliaryGraphDictUtil.update(aux_dict, other.to_dict())
        assert aux_dict == model.to_dict()

    def test_merges_attributes(self):
        model = _aux("e0", attrs=[Attribute(attribute_type_id="biolink:x", value=1)])
        other = _aux("e0", attrs=[Attribute(attribute_type_id="biolink:y", value=2)])
        aux_dict = model.to_dict()
        model.update(other)
        AuxiliaryGraphDictUtil.update(aux_dict, other.to_dict())
        assert aux_dict == model.to_dict()


class TestMergeDictionaries:
    def test_parity(self):
        old_models = {
            "a0": _aux("e0", attrs=[Attribute(attribute_type_id="biolink:x", value=1)]),
            "a1": _aux("e1"),
        }
        new_models = {
            "a1": _aux("e1", attrs=[Attribute(attribute_type_id="biolink:y", value=2)]),
            "a2": _aux("e2"),
        }
        old_dicts: dict[str, AuxiliaryGraphDict] = {
            k: v.to_dict() for k, v in old_models.items()
        }
        new_dicts: dict[str, AuxiliaryGraphDict] = {
            k: v.to_dict() for k, v in new_models.items()
        }
        AuxiliaryGraph.merge_dictionaries(old_models, new_models)
        AuxiliaryGraphDictUtil.merge_dictionaries(old_dicts, new_dicts)
        assert old_dicts == {k: v.to_dict() for k, v in old_models.items()}
