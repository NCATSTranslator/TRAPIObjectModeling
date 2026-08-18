"""Tests for translator_tom.models.analysis."""

from translator_tom import (
    Analysis,
    Attribute,
    EdgeBinding,
    PathBinding,
)
from translator_tom.model_dicts.analysis import AnalysisDictUtil


def _attr(value: int = 1, type_id: str = "biolink:foo") -> Attribute:
    return Attribute(attribute_type_id=type_id, value=value)


def _eb(*edge_ids: str) -> EdgeBinding:
    return EdgeBinding(ids=list(edge_ids) or ["e1"])


def _pb(*aux_ids: str) -> PathBinding:
    return PathBinding(ids=list(aux_ids) or ["aux1"])


class TestAnalysisConstruction:
    def test_required_fields_only(self):
        a = Analysis(resource_id="infores:foo")
        assert a.resource_id == "infores:foo"
        assert a.score is None
        assert a.support_graphs is None
        assert a.attributes is None
        assert a.edge_bindings is None
        assert a.path_bindings is None

    def test_full_construction(self):
        a = Analysis(
            resource_id="infores:foo",
            score=0.9,
            support_graphs=["aux1"],
            scoring_method="custom",
            attributes=[_attr()],
            edge_bindings={"e0": _eb("k1")},
        )
        assert a.score == 0.9


class TestAnalysisListProperties:
    def test_support_graphs_list_when_none(self):
        assert Analysis(resource_id="infores:foo").support_graphs_list == []

    def test_support_graphs_list_when_set(self):
        a = Analysis(resource_id="infores:foo", support_graphs=["g1", "g2"])
        assert a.support_graphs_list == ["g1", "g2"]

    def test_attributes_list_when_none(self):
        assert Analysis(resource_id="infores:foo").attributes_list == []

    def test_attributes_list_when_set(self):
        attr = _attr()
        a = Analysis(resource_id="infores:foo", attributes=[attr])
        assert a.attributes_list == [attr]

    def test_edge_bindings_dict_when_none(self):
        assert Analysis(resource_id="infores:foo").edge_bindings_dict == {}

    def test_path_bindings_dict_when_none(self):
        assert Analysis(resource_id="infores:foo").path_bindings_dict == {}


class TestAnalysisHash:
    def test_deterministic(self):
        a = Analysis(resource_id="infores:foo", score=0.5)
        b = Analysis(resource_id="infores:foo", score=0.5)
        assert a.hash() == b.hash()

    def test_support_graph_order_does_not_matter(self):
        # support_graphs are hashed via frozenset.
        a = Analysis(resource_id="infores:foo", support_graphs=["g1", "g2"])
        b = Analysis(resource_id="infores:foo", support_graphs=["g2", "g1"])
        assert a.hash() == b.hash()

    def test_attributes_excluded_from_hash(self):
        # Attributes are merged via `update` but not included in hash().
        a = Analysis(resource_id="infores:foo")
        b = Analysis(resource_id="infores:foo", attributes=[_attr()])
        assert a.hash() == b.hash()

    def test_score_changes_hash(self):
        a = Analysis(resource_id="infores:foo", score=0.1)
        b = Analysis(resource_id="infores:foo", score=0.2)
        assert a.hash() != b.hash()

    def test_changes_with_edge_bindings(self):
        a = Analysis(resource_id="infores:foo", edge_bindings={"e1": _eb("k1")})
        b = Analysis(resource_id="infores:foo", edge_bindings={"e1": _eb("k2")})
        assert a.hash() != b.hash()

    def test_changes_with_path_bindings(self):
        a = Analysis(resource_id="infores:foo", path_bindings={"p1": _pb("aux1")})
        b = Analysis(resource_id="infores:foo", path_bindings={"p1": _pb("aux2")})
        assert a.hash() != b.hash()


class TestAnalysisUpdateAttributesAndSupport:
    def test_assigns_attributes_when_self_has_none(self):
        a = Analysis(resource_id="infores:foo")
        b = Analysis(resource_id="infores:foo", attributes=[_attr(1)])
        a.update(b)
        assert a.attributes is not None
        assert len(a.attributes) == 1

    def test_merges_attributes_when_both_present(self):
        a = Analysis(resource_id="infores:foo", attributes=[_attr(1)])
        b = Analysis(resource_id="infores:foo", attributes=[_attr(2, "biolink:bar")])
        a.update(b)
        assert a.attributes is not None
        assert len(a.attributes) == 2

    def test_does_not_overwrite_attributes_when_other_has_none(self):
        a = Analysis(resource_id="infores:foo", attributes=[_attr(1)])
        b = Analysis(resource_id="infores:foo")
        a.update(b)
        assert a.attributes is not None
        assert len(a.attributes) == 1

    def test_assigns_support_graphs_when_self_has_none(self):
        a = Analysis(resource_id="infores:foo")
        b = Analysis(resource_id="infores:foo", support_graphs=["g1"])
        a.update(b)
        assert a.support_graphs == ["g1"]

    def test_unions_support_graphs_when_both_present(self):
        a = Analysis(resource_id="infores:foo", support_graphs=["g1", "g2"])
        b = Analysis(resource_id="infores:foo", support_graphs=["g2", "g3"])
        a.update(b)
        assert a.support_graphs is not None
        assert set(a.support_graphs) == {"g1", "g2", "g3"}


class TestAnalysisUpdateEdgeBindings:
    def test_adds_new_qedge_key(self):
        a = Analysis(resource_id="infores:foo", edge_bindings={"e1": _eb("k1")})
        b = Analysis(resource_id="infores:foo", edge_bindings={"e2": _eb("k2")})
        a.update(b)
        assert a.edge_bindings is not None
        assert set(a.edge_bindings) == {"e1", "e2"}

    def test_unions_ids_for_existing_qedge_key(self):
        a = Analysis(resource_id="infores:foo", edge_bindings={"e1": _eb("k1")})
        b = Analysis(resource_id="infores:foo", edge_bindings={"e1": _eb("k2")})
        a.update(b)
        assert a.edge_bindings is not None
        assert set(a.edge_bindings["e1"].ids) == {"k1", "k2"}

    def test_dedupes_ids_via_union(self):
        a = Analysis(resource_id="infores:foo", edge_bindings={"e1": _eb("k1")})
        b = Analysis(resource_id="infores:foo", edge_bindings={"e1": _eb("k1")})
        a.update(b)
        assert a.edge_bindings is not None
        assert a.edge_bindings["e1"].ids == ["k1"]

    def test_does_not_mutate_other(self):
        # update deepcopies bindings from `other` before assigning.
        a = Analysis(resource_id="infores:foo")
        b = Analysis(resource_id="infores:foo", edge_bindings={"e1": _eb("k1")})
        a.update(b)
        assert a.edge_bindings is not None
        a.edge_bindings["e1"].ids.append("k99")
        assert b.edge_bindings is not None
        assert b.edge_bindings["e1"].ids == ["k1"]

    def test_dedupes_ids_no_duplicates(self):
        # Overlapping ids collapse to a single deduped, order-stable list.
        a = Analysis(
            resource_id="infores:foo",
            edge_bindings={"e1": _eb("k1", "k2", "k3")},
        )
        b = Analysis(
            resource_id="infores:foo",
            edge_bindings={"e1": _eb("k2", "k3", "k4")},
        )
        a.update(b)
        merged = a.edge_bindings["e1"]
        assert merged.ids == ["k1", "k2", "k3", "k4"]
        assert len(set(merged.ids)) == len(merged.ids)

    def test_preserves_order_existing_then_new(self):
        # Existing ids retain order; genuinely-new ones append after.
        a = Analysis(
            resource_id="infores:foo",
            edge_bindings={"e1": _eb("k1", "k2")},
        )
        b = Analysis(
            resource_id="infores:foo",
            edge_bindings={"e1": _eb("k2", "k3")},
        )
        a.update(b)
        assert a.edge_bindings["e1"].ids == ["k1", "k2", "k3"]

    def test_existing_binding_kept_and_mutated_in_place(self):
        # The `self` binding object is retained (ids unioned in place), not
        # replaced by `other`'s.
        a = Analysis(resource_id="infores:foo", edge_bindings={"e1": _eb("k1")})
        kept = a.edge_bindings["e1"]
        b = Analysis(resource_id="infores:foo", edge_bindings={"e1": _eb("k1")})
        a.update(b)
        assert a.edge_bindings["e1"] is kept

    def test_other_bindings_unchanged_after_update(self):
        # `other`'s bindings are untouched by the merge.
        a = Analysis(resource_id="infores:foo", edge_bindings={"e1": _eb("k1")})
        b = Analysis(
            resource_id="infores:foo",
            edge_bindings={"e1": _eb("k2"), "e2": _eb("k3")},
        )
        b_hash_before = b.hash()
        a.update(b)
        assert b.hash() == b_hash_before
        assert b.edge_bindings["e1"].ids == ["k2"]
        assert b.edge_bindings["e2"].ids == ["k3"]

    def test_update_hash_parity_with_dict_util(self):
        # Model.update and AnalysisDictUtil.update yield hash-equal results.
        a = Analysis(
            resource_id="infores:foo",
            support_graphs=["g0"],
            edge_bindings={"e1": _eb("k1", "k2"), "e2": _eb("k5")},
        )
        b = Analysis(
            resource_id="infores:foo",
            support_graphs=["g1"],
            edge_bindings={"e1": _eb("k2", "k3"), "e3": _eb("k7")},
        )
        a_dict = a.to_dict()
        a.update(b)
        AnalysisDictUtil.update(a_dict, b.to_dict())
        assert AnalysisDictUtil.hash(a_dict) == a.hash()


class TestAnalysisUpdatePathBindings:
    def test_adds_new_qpath_key(self):
        a = Analysis(resource_id="infores:foo", path_bindings={"p1": _pb("aux1")})
        b = Analysis(resource_id="infores:foo", path_bindings={"p2": _pb("aux2")})
        a.update(b)
        assert a.path_bindings is not None
        assert set(a.path_bindings) == {"p1", "p2"}

    def test_unions_ids_for_existing_qpath_key(self):
        a = Analysis(resource_id="infores:foo", path_bindings={"p1": _pb("aux1")})
        b = Analysis(resource_id="infores:foo", path_bindings={"p1": _pb("aux2")})
        a.update(b)
        assert a.path_bindings is not None
        assert set(a.path_bindings["p1"].ids) == {"aux1", "aux2"}

    def test_does_not_mutate_other(self):
        # update deepcopies bindings from `other` before assigning.
        a = Analysis(resource_id="infores:foo")
        b = Analysis(resource_id="infores:foo", path_bindings={"p1": _pb("aux1")})
        a.update(b)
        assert a.path_bindings is not None
        a.path_bindings["p1"].ids.append("aux99")
        assert b.path_bindings is not None
        assert b.path_bindings["p1"].ids == ["aux1"]

    def test_dedupes_ids_no_duplicates(self):
        # Overlapping ids collapse to a single deduped, order-stable list.
        a = Analysis(
            resource_id="infores:foo",
            path_bindings={"p1": _pb("aux1", "aux2")},
        )
        b = Analysis(
            resource_id="infores:foo",
            path_bindings={"p1": _pb("aux2", "aux3")},
        )
        a.update(b)
        merged = a.path_bindings["p1"]
        assert merged.ids == ["aux1", "aux2", "aux3"]
        assert len(set(merged.ids)) == len(merged.ids)

    def test_other_bindings_unchanged_after_update(self):
        a = Analysis(resource_id="infores:foo", path_bindings={"p1": _pb("aux1")})
        b = Analysis(resource_id="infores:foo", path_bindings={"p1": _pb("aux2")})
        b_hash_before = b.hash()
        a.update(b)
        assert b.hash() == b_hash_before
        assert b.path_bindings is not None
        assert b.path_bindings["p1"].ids == ["aux2"]

    def test_update_hash_parity_with_dict_util(self):
        # Model.update and AnalysisDictUtil.update yield hash-equal results.
        a = Analysis(
            resource_id="infores:foo",
            path_bindings={"p1": _pb("aux1"), "p2": _pb("aux5")},
        )
        b = Analysis(
            resource_id="infores:foo",
            path_bindings={"p1": _pb("aux2"), "p3": _pb("aux7")},
        )
        a_dict = a.to_dict()
        a.update(b)
        AnalysisDictUtil.update(a_dict, b.to_dict())
        assert AnalysisDictUtil.hash(a_dict) == a.hash()
