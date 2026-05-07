"""Tests for translator_tom.models.analysis."""

from translator_tom import (
    Analysis,
    Attribute,
    BaseAnalysis,
    EdgeBinding,
    PathBinding,
    PathfinderAnalysis,
)


def _attr(value: int = 1, type_id: str = "biolink:foo") -> Attribute:
    return Attribute(attribute_type_id=type_id, value=value)


def _eb(edge_id: str = "e1", attrs: list[Attribute] | None = None) -> EdgeBinding:
    return EdgeBinding(id=edge_id, attributes=attrs or [])


class TestBaseAnalysisConstruction:
    def test_required_fields_only(self):
        a = BaseAnalysis(resource_id="infores:foo")
        assert a.resource_id == "infores:foo"
        assert a.score is None
        assert a.support_graphs is None
        assert a.attributes is None

    def test_full_construction(self):
        a = BaseAnalysis(
            resource_id="infores:foo",
            score=0.9,
            support_graphs=["aux1"],
            scoring_method="custom",
            attributes=[_attr()],
        )
        assert a.score == 0.9


class TestBaseAnalysisListProperties:
    def test_support_graphs_list_when_none(self):
        assert BaseAnalysis(resource_id="infores:foo").support_graphs_list == []

    def test_support_graphs_list_when_set(self):
        a = BaseAnalysis(resource_id="infores:foo", support_graphs=["g1", "g2"])
        assert a.support_graphs_list == ["g1", "g2"]

    def test_attributes_list_when_none(self):
        assert BaseAnalysis(resource_id="infores:foo").attributes_list == []

    def test_attributes_list_when_set(self):
        attr = _attr()
        a = BaseAnalysis(resource_id="infores:foo", attributes=[attr])
        assert a.attributes_list == [attr]


class TestBaseAnalysisHash:
    def test_deterministic(self):
        a = BaseAnalysis(resource_id="infores:foo", score=0.5)
        b = BaseAnalysis(resource_id="infores:foo", score=0.5)
        assert a.hash() == b.hash()

    def test_support_graph_order_does_not_matter(self):
        # support_graphs are hashed via frozenset.
        a = BaseAnalysis(resource_id="infores:foo", support_graphs=["g1", "g2"])
        b = BaseAnalysis(resource_id="infores:foo", support_graphs=["g2", "g1"])
        assert a.hash() == b.hash()

    def test_attributes_excluded_from_hash(self):
        # Attributes are merged via `_update_base` but not included in hash().
        a = BaseAnalysis(resource_id="infores:foo")
        b = BaseAnalysis(resource_id="infores:foo", attributes=[_attr()])
        assert a.hash() == b.hash()

    def test_score_changes_hash(self):
        a = BaseAnalysis(resource_id="infores:foo", score=0.1)
        b = BaseAnalysis(resource_id="infores:foo", score=0.2)
        assert a.hash() != b.hash()


class TestBaseAnalysisUpdateBase:
    def test_assigns_attributes_when_self_has_none(self):
        a = BaseAnalysis(resource_id="infores:foo")
        b = BaseAnalysis(resource_id="infores:foo", attributes=[_attr(1)])
        a._update_base(b)
        assert a.attributes is not None
        assert len(a.attributes) == 1

    def test_merges_attributes_when_both_present(self):
        a = BaseAnalysis(resource_id="infores:foo", attributes=[_attr(1)])
        b = BaseAnalysis(
            resource_id="infores:foo", attributes=[_attr(2, "biolink:bar")]
        )
        a._update_base(b)
        assert a.attributes is not None
        assert len(a.attributes) == 2

    def test_does_not_overwrite_attributes_when_other_has_none(self):
        a = BaseAnalysis(resource_id="infores:foo", attributes=[_attr(1)])
        b = BaseAnalysis(resource_id="infores:foo")
        a._update_base(b)
        assert a.attributes is not None
        assert len(a.attributes) == 1

    def test_assigns_support_graphs_when_self_has_none(self):
        a = BaseAnalysis(resource_id="infores:foo")
        b = BaseAnalysis(resource_id="infores:foo", support_graphs=["g1"])
        a._update_base(b)
        assert a.support_graphs == ["g1"]

    def test_unions_support_graphs_when_both_present(self):
        a = BaseAnalysis(resource_id="infores:foo", support_graphs=["g1", "g2"])
        b = BaseAnalysis(resource_id="infores:foo", support_graphs=["g2", "g3"])
        a._update_base(b)
        assert a.support_graphs is not None
        assert set(a.support_graphs) == {"g1", "g2", "g3"}


class TestAnalysisHash:
    def test_deterministic(self):
        a = Analysis(
            resource_id="infores:foo",
            edge_bindings={"e1": [_eb("k1")]},
        )
        b = Analysis(
            resource_id="infores:foo",
            edge_bindings={"e1": [_eb("k1")]},
        )
        assert a.hash() == b.hash()

    def test_changes_with_edge_bindings(self):
        a = Analysis(
            resource_id="infores:foo",
            edge_bindings={"e1": [_eb("k1")]},
        )
        b = Analysis(
            resource_id="infores:foo",
            edge_bindings={"e1": [_eb("k2")]},
        )
        assert a.hash() != b.hash()

    def test_binding_order_does_not_matter(self):
        # Bindings are hashed via frozenset.
        a = Analysis(
            resource_id="infores:foo",
            edge_bindings={"e1": [_eb("k1"), _eb("k2")]},
        )
        b = Analysis(
            resource_id="infores:foo",
            edge_bindings={"e1": [_eb("k2"), _eb("k1")]},
        )
        assert a.hash() == b.hash()


class TestAnalysisUpdate:
    def test_adds_new_qedge_key(self):
        a = Analysis(
            resource_id="infores:foo", edge_bindings={"e1": [_eb("k1")]}
        )
        b = Analysis(
            resource_id="infores:foo", edge_bindings={"e2": [_eb("k2")]}
        )
        a.update(b)
        assert set(a.edge_bindings) == {"e1", "e2"}

    def test_unions_existing_qedge_key(self):
        a = Analysis(
            resource_id="infores:foo", edge_bindings={"e1": [_eb("k1")]}
        )
        b = Analysis(
            resource_id="infores:foo", edge_bindings={"e1": [_eb("k2")]}
        )
        a.update(b)
        assert {b.id for b in a.edge_bindings["e1"]} == {"k1", "k2"}

    def test_dedupes_via_set_union(self):
        a = Analysis(
            resource_id="infores:foo", edge_bindings={"e1": [_eb("k1")]}
        )
        b = Analysis(
            resource_id="infores:foo", edge_bindings={"e1": [_eb("k1")]}
        )
        a.update(b)
        assert len(a.edge_bindings["e1"]) == 1

    def test_does_not_mutate_other(self):
        # update deepcopies bindings from `other` before assigning.
        a = Analysis(resource_id="infores:foo", edge_bindings={})
        b = Analysis(
            resource_id="infores:foo", edge_bindings={"e1": [_eb("k1")]}
        )
        a.update(b)
        a.edge_bindings["e1"].append(_eb("k99"))
        assert len(b.edge_bindings["e1"]) == 1


class TestPathfinderAnalysisHash:
    def test_deterministic(self):
        a = PathfinderAnalysis(
            resource_id="infores:foo",
            path_bindings={"p1": [PathBinding(id="aux1")]},
        )
        b = PathfinderAnalysis(
            resource_id="infores:foo",
            path_bindings={"p1": [PathBinding(id="aux1")]},
        )
        assert a.hash() == b.hash()

    def test_changes_with_path_bindings(self):
        a = PathfinderAnalysis(
            resource_id="infores:foo",
            path_bindings={"p1": [PathBinding(id="aux1")]},
        )
        b = PathfinderAnalysis(
            resource_id="infores:foo",
            path_bindings={"p1": [PathBinding(id="aux2")]},
        )
        assert a.hash() != b.hash()


class TestPathfinderAnalysisUpdate:
    def test_adds_new_qpath_key(self):
        a = PathfinderAnalysis(
            resource_id="infores:foo",
            path_bindings={"p1": [PathBinding(id="aux1")]},
        )
        b = PathfinderAnalysis(
            resource_id="infores:foo",
            path_bindings={"p2": [PathBinding(id="aux2")]},
        )
        a.update(b)
        assert set(a.path_bindings) == {"p1", "p2"}

    def test_unions_existing_qpath_key(self):
        a = PathfinderAnalysis(
            resource_id="infores:foo",
            path_bindings={"p1": [PathBinding(id="aux1")]},
        )
        b = PathfinderAnalysis(
            resource_id="infores:foo",
            path_bindings={"p1": [PathBinding(id="aux2")]},
        )
        a.update(b)
        assert {pb.id for pb in a.path_bindings["p1"]} == {"aux1", "aux2"}

    def test_does_not_mutate_other(self):
        a = PathfinderAnalysis(resource_id="infores:foo", path_bindings={})
        b = PathfinderAnalysis(
            resource_id="infores:foo",
            path_bindings={"p1": [PathBinding(id="aux1")]},
        )
        a.update(b)
        a.path_bindings["p1"].append(PathBinding(id="aux99"))
        assert len(b.path_bindings["p1"]) == 1
