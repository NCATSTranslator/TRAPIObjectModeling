"""Hash-parity tests for the binding `*DictUtil` classes (edge/node/path)."""

from __future__ import annotations

from translator_tom.v1_6.model_dicts.edge_binding import EdgeBindingDictUtil
from translator_tom.v1_6.model_dicts.node_binding import NodeBindingDictUtil
from translator_tom.v1_6.model_dicts.path_binding import PathBindingDictUtil
from translator_tom.v1_6.models.attribute import Attribute
from translator_tom.v1_6.models.edge_binding import EdgeBinding
from translator_tom.v1_6.models.node_binding import NodeBinding
from translator_tom.v1_6.models.path_binding import PathBinding


def _attrs() -> list[Attribute]:
    return [
        Attribute(attribute_type_id="biolink:score", value=0.9),
        Attribute(attribute_type_id="biolink:source", value="infores:x"),
    ]


class TestEdgeBindingHashParity:
    def test_no_attributes(self):
        eb = EdgeBinding(id="e0", attributes=[])
        assert EdgeBindingDictUtil.hash(eb.to_dict()) == eb.hash()

    def test_with_attributes(self):
        eb = EdgeBinding(id="e0", attributes=_attrs())
        assert EdgeBindingDictUtil.hash(eb.to_dict()) == eb.hash()


class TestNodeBindingHashParity:
    def test_minimal(self):
        nb = NodeBinding(id="CHEBI:1", attributes=[])
        assert NodeBindingDictUtil.hash(nb.to_dict()) == nb.hash()

    def test_with_query_id_and_attributes(self):
        nb = NodeBinding(id="CHEBI:1", query_id="MONDO:1", attributes=_attrs())
        assert NodeBindingDictUtil.hash(nb.to_dict()) == nb.hash()


class TestPathBindingHashParity:
    def test_base_hash(self):
        pb = PathBinding(id="a0")
        assert PathBindingDictUtil.hash(pb.to_dict()) == pb.hash()
