"""Hash-parity tests for the binding `*DictUtil` classes (edge/node/path).

In TRAPI 2.0 a binding is a single object carrying an `ids` list (no per-binding
`id`/`query_id`/`attributes`); its hash is the frozenset of those ids.
"""

from __future__ import annotations

from translator_tom.v2_0.model_dicts.edge_binding import EdgeBindingDictUtil
from translator_tom.v2_0.model_dicts.node_binding import NodeBindingDictUtil
from translator_tom.v2_0.model_dicts.path_binding import PathBindingDictUtil
from translator_tom.v2_0.models.edge_binding import EdgeBinding
from translator_tom.v2_0.models.node_binding import NodeBinding
from translator_tom.v2_0.models.path_binding import PathBinding


class TestEdgeBindingHashParity:
    def test_single_id(self):
        eb = EdgeBinding(ids=["e0"])
        assert EdgeBindingDictUtil.hash(eb.to_dict()) == eb.hash()

    def test_multiple_ids(self):
        eb = EdgeBinding(ids=["e0", "e1"])
        assert EdgeBindingDictUtil.hash(eb.to_dict()) == eb.hash()


class TestNodeBindingHashParity:
    def test_single_id(self):
        nb = NodeBinding(ids=["CHEBI:1"])
        assert NodeBindingDictUtil.hash(nb.to_dict()) == nb.hash()

    def test_multiple_ids(self):
        nb = NodeBinding(ids=["CHEBI:1", "MONDO:1"])
        assert NodeBindingDictUtil.hash(nb.to_dict()) == nb.hash()


class TestPathBindingHashParity:
    def test_single_id(self):
        pb = PathBinding(ids=["a0"])
        assert PathBindingDictUtil.hash(pb.to_dict()) == pb.hash()

    def test_multiple_ids(self):
        pb = PathBinding(ids=["a0", "a1"])
        assert PathBindingDictUtil.hash(pb.to_dict()) == pb.hash()
