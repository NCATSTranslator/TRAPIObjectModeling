"""Tests for translator_tom.v2_0.models.knowledge_graph."""

import pytest
from pydantic import ValidationError

from translator_tom import (
    Analysis,
    Attribute,
    AttributeConstraint,
    AuxiliaryGraph,
    Edge,
    EdgeBinding,
    KnowledgeGraph,
    Node,
    NodeBinding,
    PathBinding,
    Qualifier,
    Result,
    RetrievalSource,
)


def _src(
    resource_id: str = "infores:foo",
    role: str = "primary_knowledge_source",
    upstream: list[str] | None = None,
) -> RetrievalSource:
    return RetrievalSource(
        resource_id=resource_id,
        resource_role=role,  # type: ignore[arg-type]
        upstream_resource_ids=upstream,
    )


def _node(name: str = "Alice", categories: list[str] | None = None) -> Node:
    return Node(
        name=name,
        categories=categories or ["biolink:NamedThing"],
        attributes=[],
    )


def _edge(  # noqa: PLR0913  (test helper: all edge fields need to be overridable)
    subject: str = "A:1",
    object_: str = "B:2",
    predicate: str = "biolink:related_to",
    sources: list[RetrievalSource] | None = None,
    attributes: list[Attribute] | None = None,
    qualifiers: list[Qualifier] | None = None,
    knowledge_level: str = "knowledge_assertion",
    agent_type: str = "manual_agent",
) -> Edge:
    return Edge(
        predicate=predicate,
        subject=subject,
        object=object_,
        sources=sources or [_src()],
        attributes=attributes,
        qualifiers=qualifiers,
        knowledge_level=knowledge_level,
        agent_type=agent_type,
    )


# ============================================================================
# KnowledgeGraph
# ============================================================================


class TestKnowledgeGraphNew:
    def test_new_empty(self):
        kg = KnowledgeGraph.new()
        assert kg.nodes == {}
        assert kg.edges == {}

    def test_new_without_edges(self):
        kg = KnowledgeGraph.new(edges=False)
        assert kg.nodes == {}
        assert kg.edges is None


class TestKnowledgeGraphNormalize:
    def test_rekeys_edges_by_hash(self):
        edge = _edge()
        kg = KnowledgeGraph(nodes={}, edges={"old_id": edge})
        mapping = kg.normalize()
        assert "old_id" in mapping
        assert mapping["old_id"] == edge.hash()
        assert kg.edges is not None
        assert edge.hash() in kg.edges
        assert "old_id" not in kg.edges


class TestKnowledgeGraphUpdate:
    def test_neither_pre_normalized_normalizes_both(self):
        edge_a = _edge()
        edge_b = _edge(subject="A:9")
        kg_a = KnowledgeGraph(nodes={}, edges={"old_a": edge_a})
        kg_b = KnowledgeGraph(nodes={}, edges={"old_b": edge_b})
        self_mapping, other_mapping = kg_a.update(kg_b)
        assert "old_a" in self_mapping
        assert "old_b" in other_mapping
        # kg_a should now have both edges keyed by hash
        assert kg_a.edges is not None
        assert edge_a.hash() in kg_a.edges
        assert edge_b.hash() in kg_a.edges

    def test_both_pre_normalized_no_renaming(self):
        edge_a = _edge()
        edge_b = _edge(subject="A:9")
        kg_a = KnowledgeGraph(nodes={}, edges={"keep_a": edge_a})
        kg_b = KnowledgeGraph(nodes={}, edges={"keep_b": edge_b})
        self_mapping, other_mapping = kg_a.update(kg_b, pre_normalized="both")
        assert self_mapping == {}
        assert other_mapping == {}
        assert kg_a.edges is not None
        assert "keep_a" in kg_a.edges
        assert "keep_b" in kg_a.edges

    def test_self_pre_normalized_only_normalizes_other(self):
        edge_a = _edge()
        edge_b = _edge(subject="A:9")
        kg_a = KnowledgeGraph(nodes={}, edges={"keep_a": edge_a})
        kg_b = KnowledgeGraph(nodes={}, edges={"old_b": edge_b})
        self_mapping, other_mapping = kg_a.update(kg_b, pre_normalized="self")
        assert self_mapping == {}
        assert "old_b" in other_mapping
        assert kg_a.edges is not None
        assert "keep_a" in kg_a.edges
        assert edge_b.hash() in kg_a.edges

    def test_other_pre_normalized_only_normalizes_self(self):
        edge_a = _edge()
        edge_b = _edge(subject="A:9")
        kg_a = KnowledgeGraph(nodes={}, edges={"old_a": edge_a})
        kg_b = KnowledgeGraph(nodes={}, edges={"keep_b": edge_b})
        self_mapping, other_mapping = kg_a.update(kg_b, pre_normalized="other")
        assert "old_a" in self_mapping
        assert other_mapping == {}
        assert kg_a.edges is not None
        assert edge_a.hash() in kg_a.edges
        assert "keep_b" in kg_a.edges

    def test_colliding_old_ids_are_not_conflated(self):
        # self and other reuse the same old id for DIFFERENT edges; the two remaps
        # must stay separate rather than clobber each other in one flat mapping.
        edge_a = _edge()
        edge_b = _edge(subject="A:9")
        kg_a = KnowledgeGraph(nodes={}, edges={"e0": edge_a})
        kg_b = KnowledgeGraph(nodes={}, edges={"e0": edge_b})
        self_mapping, other_mapping = kg_a.update(kg_b)
        assert self_mapping["e0"] == edge_a.hash()
        assert other_mapping["e0"] == edge_b.hash()
        # both edges are present under their distinct hashes
        assert edge_a.hash() in kg_a.edges
        assert edge_b.hash() in kg_a.edges

    def test_does_not_mutate_other_kg(self):
        edge_b = _edge(subject="A:9")
        kg_a = KnowledgeGraph.new()
        kg_b = KnowledgeGraph(nodes={}, edges={"old_b": edge_b})
        kg_a.update(kg_b)
        # other should retain its original key
        assert kg_b.edges is not None
        assert "old_b" in kg_b.edges

    def test_merges_existing_nodes(self):
        node_a = _node(name="Alice")
        node_b = _node(name="Bob", categories=["biolink:Gene"])
        kg_a = KnowledgeGraph(nodes={"N:1": node_a}, edges={})
        kg_b = KnowledgeGraph(nodes={"N:1": node_b}, edges={})
        kg_a.update(kg_b, pre_normalized="both")
        # name is updated and categories unioned
        assert kg_a.nodes["N:1"].name == "Bob"
        assert set(kg_a.nodes["N:1"].categories) == {
            "biolink:NamedThing",
            "biolink:Gene",
        }

    def test_adds_new_nodes(self):
        kg_a = KnowledgeGraph.new()
        kg_b = KnowledgeGraph(nodes={"N:1": _node()}, edges={})
        kg_a.update(kg_b, pre_normalized="both")
        assert "N:1" in kg_a.nodes


class TestKnowledgeGraphPrune:
    def _build_result(self, node_ids: list[str], edge_ids: list[str]) -> Result:
        return Result(
            node_bindings={"n0": NodeBinding(ids=node_ids)},
            analyses=[
                Analysis(
                    resource_id="infores:test",
                    edge_bindings={"e0": EdgeBinding(ids=edge_ids)},
                )
            ],
        )

    def test_removes_unbound_nodes_and_edges(self):
        kg = KnowledgeGraph(
            nodes={"A:1": _node(), "A:2": _node(), "A:3": _node()},
            edges={
                "e1": _edge(subject="A:1", object_="A:2"),
                "e2": _edge(subject="A:2", object_="A:3"),
            },
        )
        result = self._build_result(["A:1"], ["e1"])
        kg.prune({}, [result])
        # e1 keeps A:1 and A:2 bound; A:3 and e2 are pruned.
        assert kg.edges is not None
        assert set(kg.edges) == {"e1"}
        assert set(kg.nodes) == {"A:1", "A:2"}

    def test_follows_support_graph_chain(self):
        # e1 is bound directly. e1 references aux-1, which contains e2.
        # So e2 should be kept too.
        e1 = _edge(
            subject="A:1",
            object_="A:2",
            attributes=[
                Attribute(attribute_type_id="biolink:support_graphs", value=["aux-1"])
            ],
        )
        e2 = _edge(subject="A:3", object_="A:4")
        kg = KnowledgeGraph(
            nodes={
                "A:1": _node(),
                "A:2": _node(),
                "A:3": _node(),
                "A:4": _node(),
            },
            edges={"e1": e1, "e2": e2},
        )
        aux = {"aux-1": AuxiliaryGraph(edges=["e2"])}
        result = self._build_result(["A:1"], ["e1"])
        kg.prune(aux, [result])
        assert kg.edges is not None
        assert set(kg.edges) == {"e1", "e2"}

    def test_cycle_prevention_in_support_graphs(self):
        # e1 -> aux-1 -> e1 forms a cycle. prune must not loop forever.
        e1 = _edge(
            subject="A:1",
            object_="A:2",
            attributes=[
                Attribute(attribute_type_id="biolink:support_graphs", value=["aux-1"])
            ],
        )
        kg = KnowledgeGraph(
            nodes={"A:1": _node(), "A:2": _node()},
            edges={"e1": e1},
        )
        aux = {"aux-1": AuxiliaryGraph(edges=["e1"])}
        result = self._build_result(["A:1"], ["e1"])
        kg.prune(aux, [result])  # would hang if cycle prevention failed
        assert kg.edges is not None
        assert "e1" in kg.edges

    def test_pathfinder_analysis_paths_keep_edges(self):
        # A path-binding analysis references an aux graph whose edges
        # should be kept.
        e1 = _edge(subject="A:1", object_="A:2")
        kg = KnowledgeGraph(
            nodes={"A:1": _node(), "A:2": _node()},
            edges={"e1": e1, "unused": _edge(subject="X:1", object_="X:2")},
        )
        aux = {"aux-p": AuxiliaryGraph(edges=["e1"])}
        result = Result(
            node_bindings={"n0": NodeBinding(ids=["A:1"])},
            analyses=[
                Analysis(
                    resource_id="infores:test",
                    path_bindings={"p0": PathBinding(ids=["aux-p"])},
                )
            ],
        )
        kg.prune(aux, [result])
        assert kg.edges is not None
        assert "e1" in kg.edges
        assert "unused" not in kg.edges

    def test_analysis_support_graphs_keep_aux_edges(self):
        # An Analysis lists an aux graph in its support_graphs field. Edges in
        # that aux graph (and their endpoint nodes) should be kept, and any
        # biolink:support_graphs attribute on those edges should be followed
        # transitively.
        e_bound = _edge(subject="A:1", object_="A:2")
        e_supporting = _edge(
            subject="A:3",
            object_="A:4",
            attributes=[
                Attribute(attribute_type_id="biolink:support_graphs", value=["aux-2"])
            ],
        )
        e_nested = _edge(subject="A:5", object_="A:6")
        e_unused = _edge(subject="X:1", object_="X:2")
        kg = KnowledgeGraph(
            nodes={
                "A:1": _node(),
                "A:2": _node(),
                "A:3": _node(),
                "A:4": _node(),
                "A:5": _node(),
                "A:6": _node(),
                "X:1": _node(),
                "X:2": _node(),
            },
            edges={
                "e_bound": e_bound,
                "e_supporting": e_supporting,
                "e_nested": e_nested,
                "e_unused": e_unused,
            },
        )
        aux = {
            "aux-1": AuxiliaryGraph(edges=["e_supporting"]),
            "aux-2": AuxiliaryGraph(edges=["e_nested"]),
        }
        result = Result(
            node_bindings={"n0": NodeBinding(ids=["A:1"])},
            analyses=[
                Analysis(
                    resource_id="infores:test",
                    edge_bindings={"e0": EdgeBinding(ids=["e_bound"])},
                    support_graphs=["aux-1"],
                )
            ],
        )
        kg.prune(aux, [result])
        assert kg.edges is not None
        assert set(kg.edges) == {"e_bound", "e_supporting", "e_nested"}
        assert set(kg.nodes) == {"A:1", "A:2", "A:3", "A:4", "A:5", "A:6"}

    def test_prune_with_empty_results_keeps_nothing(self):
        kg = KnowledgeGraph(nodes={"A:1": _node()}, edges={"e1": _edge()})
        kg.prune({}, [])
        assert kg.nodes == {}
        # No bound edges: the empty edge dict collapses to None (empties omitted).
        assert kg.edges is None


# ============================================================================
# Node
# ============================================================================


class TestNodeBasics:
    def test_required_fields(self):
        n = _node()
        assert n.name == "Alice"
        assert n.categories == ["biolink:NamedThing"]

    def test_categories_min_length_enforced(self):
        with pytest.raises(ValidationError):
            Node(name="x", categories=[], attributes=[])

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            Node(
                name="x",
                categories=["biolink:NamedThing"],
                attributes=[],
                bogus="x",  # type: ignore[call-arg]
            )


class TestNodeHash:
    def test_only_depends_on_name_and_is_set(self):
        # categories and attributes are explicitly excluded from hash().
        a = Node(name="Alice", categories=["biolink:NamedThing"], attributes=[])
        b = Node(
            name="Alice",
            categories=["biolink:Gene"],
            attributes=[Attribute(attribute_type_id="biolink:foo", value=1)],
        )
        assert a.hash() == b.hash()

    def test_changes_with_name(self):
        a = _node(name="Alice")
        b = _node(name="Bob")
        assert a.hash() != b.hash()

    def test_changes_with_is_set(self):
        a = Node(
            name="x", categories=["biolink:NamedThing"], attributes=[], is_set=True
        )
        b = Node(
            name="x",
            categories=["biolink:NamedThing"],
            attributes=[],
            is_set=False,
        )
        assert a.hash() != b.hash()


class TestNodeMeetsConstraints:
    def test_no_constraints_returns_true(self):
        n = Node(
            name="x",
            categories=["biolink:NamedThing"],
            attributes=[Attribute(attribute_type_id="biolink:foo", value=1)],
        )
        assert n.meets_constraints([]) is True

    def test_constraint_satisfied(self):
        n = Node(
            name="x",
            categories=["biolink:NamedThing"],
            attributes=[Attribute(attribute_type_id="biolink:foo", value=1)],
        )
        c = AttributeConstraint(id="biolink:foo", name="foo", operator="==", value=1)
        assert n.meets_constraints([c]) is True

    def test_constraint_unsatisfied(self):
        n = Node(
            name="x",
            categories=["biolink:NamedThing"],
            attributes=[Attribute(attribute_type_id="biolink:foo", value=1)],
        )
        c = AttributeConstraint(id="biolink:foo", name="foo", operator="==", value=99)
        assert n.meets_constraints([c]) is False


class TestNodeUpdate:
    def test_overwrites_name_when_other_has_one(self):
        a = _node(name="Alice")
        b = _node(name="Bob")
        a.update(b)
        assert a.name == "Bob"

    def test_keeps_name_when_other_has_none(self):
        a = _node(name="Alice")
        b = Node(name=None, categories=["biolink:NamedThing"], attributes=[])
        a.update(b)
        assert a.name == "Alice"

    def test_unions_categories(self):
        a = _node(categories=["biolink:NamedThing"])
        b = _node(categories=["biolink:Gene"])
        a.update(b)
        assert set(a.categories) == {"biolink:NamedThing", "biolink:Gene"}

    def test_dedupes_attributes_by_hash(self):
        attr = Attribute(attribute_type_id="biolink:foo", value=1)
        a = Node(name="x", categories=["biolink:NamedThing"], attributes=[attr])
        b = Node(
            name="x",
            categories=["biolink:NamedThing"],
            attributes=[
                Attribute(attribute_type_id="biolink:foo", value=1),
                Attribute(attribute_type_id="biolink:bar", value=2),
            ],
        )
        a.update(b)
        # one new biolink:foo (replaces existing) + biolink:bar
        assert a.attributes is not None
        assert len(a.attributes) == 2


# ============================================================================
# Edge
# ============================================================================


class TestEdgeBasics:
    def test_required_fields(self):
        e = _edge()
        assert e.subject == "A:1"
        assert e.object == "B:2"
        assert e.predicate == "biolink:related_to"
        assert e.knowledge_level == "knowledge_assertion"
        assert e.agent_type == "manual_agent"

    def test_sources_min_length_enforced(self):
        with pytest.raises(ValidationError):
            Edge(
                predicate="biolink:related_to",
                subject="A:1",
                object="B:2",
                sources=[],
                knowledge_level="knowledge_assertion",
                agent_type="manual_agent",
            )

    def test_knowledge_level_required(self):
        with pytest.raises(ValidationError):
            Edge(
                predicate="biolink:related_to",
                subject="A:1",
                object="B:2",
                sources=[_src()],
                agent_type="manual_agent",  # type: ignore[call-arg]
            )

    def test_agent_type_required(self):
        with pytest.raises(ValidationError):
            Edge(
                predicate="biolink:related_to",
                subject="A:1",
                object="B:2",
                sources=[_src()],
                knowledge_level="knowledge_assertion",  # type: ignore[call-arg]
            )

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            Edge(
                predicate="biolink:related_to",
                subject="A:1",
                object="B:2",
                sources=[_src()],
                knowledge_level="knowledge_assertion",
                agent_type="manual_agent",
                bogus="x",  # type: ignore[call-arg]
            )


class TestEdgeProperties:
    def test_attributes_list_when_none(self):
        assert _edge().attributes_list == []

    def test_qualifiers_list_when_none(self):
        assert _edge().qualifiers_list == []

    def test_primary_knowledge_source(self):
        e = _edge(
            sources=[
                _src("infores:agg", "aggregator_knowledge_source"),
                _src("infores:primary", "primary_knowledge_source"),
            ]
        )
        assert e.primary_knowledge_source.resource_id == "infores:primary"

    def test_primary_knowledge_source_missing_raises(self):
        e = _edge(sources=[_src("infores:agg", "aggregator_knowledge_source")])
        with pytest.raises(ValueError, match="primary_knowledge_source"):
            _ = e.primary_knowledge_source

    def test_last_downstream_source(self):
        # Aggregator has primary as upstream; aggregator is the most downstream.
        e = _edge(
            sources=[
                _src("infores:primary", "primary_knowledge_source"),
                _src(
                    "infores:agg",
                    "aggregator_knowledge_source",
                    upstream=["infores:primary"],
                ),
            ]
        )
        last = e.last_downstream_source
        assert last is not None
        assert last.resource_id == "infores:agg"

    def test_is_self_edge_true(self):
        assert _edge(subject="X:1", object_="X:1").is_self_edge is True

    def test_is_self_edge_false(self):
        assert _edge().is_self_edge is False

    def test_support_graphs(self):
        e = _edge(
            attributes=[
                Attribute(
                    attribute_type_id="biolink:support_graphs",
                    value=["aux-1", "aux-2"],
                ),
                Attribute(attribute_type_id="biolink:other", value=1),
            ]
        )
        assert e.support_graphs == ["aux-1", "aux-2"]

    def test_support_graphs_empty_when_none(self):
        assert _edge().support_graphs == []


class TestEdgeHash:
    def test_attributes_excluded_from_hash(self):
        a = _edge(attributes=[Attribute(attribute_type_id="biolink:x", value=1)])
        b = _edge(attributes=[Attribute(attribute_type_id="biolink:x", value=2)])
        assert a.hash() == b.hash()

    def test_knowledge_level_and_agent_type_excluded_from_hash(self):
        a = _edge(knowledge_level="knowledge_assertion", agent_type="manual_agent")
        b = _edge(knowledge_level="prediction", agent_type="automated_agent")
        assert a.hash() == b.hash()

    def test_changes_with_subject(self):
        a = _edge(subject="A:1")
        b = _edge(subject="A:9")
        assert a.hash() != b.hash()

    def test_changes_with_predicate(self):
        a = _edge(predicate="biolink:related_to")
        b = _edge(predicate="biolink:treats")
        assert a.hash() != b.hash()

    def test_qualifier_order_does_not_matter(self):
        q1 = Qualifier(
            qualifier_type_id="biolink:subject_aspect_qualifier",
            qualifier_value="activity",
        )
        q2 = Qualifier(
            qualifier_type_id="biolink:object_aspect_qualifier",
            qualifier_value="abundance",
        )
        a = _edge(qualifiers=[q1, q2])
        b = _edge(qualifiers=[q2, q1])
        assert a.hash() == b.hash()


class TestEdgeUpdate:
    def test_assigns_attributes_when_self_empty(self):
        a = _edge()
        b = _edge(attributes=[Attribute(attribute_type_id="biolink:foo", value=1)])
        a.update(b)
        assert a.attributes is not None
        assert len(a.attributes) == 1

    def test_merges_attributes(self):
        a = _edge(attributes=[Attribute(attribute_type_id="biolink:a", value=1)])
        b = _edge(attributes=[Attribute(attribute_type_id="biolink:b", value=2)])
        a.update(b)
        assert a.attributes is not None
        assert len(a.attributes) == 2

    def test_knowledge_level_and_agent_type_new_wins(self):
        # In 2.0 KL/AT are top-level fields; update takes the other's values.
        a = _edge(knowledge_level="knowledge_assertion", agent_type="manual_agent")
        b = _edge(knowledge_level="prediction", agent_type="automated_agent")
        a.update(b)
        assert a.knowledge_level == "prediction"
        assert a.agent_type == "automated_agent"

    def test_merges_sources_with_upstream_union(self):
        a_src = _src(
            "infores:agg",
            "aggregator_knowledge_source",
            upstream=["infores:up1"],
        )
        b_src = _src(
            "infores:agg",
            "aggregator_knowledge_source",
            upstream=["infores:up2"],
        )
        a = _edge(sources=[_src(), a_src])
        b = _edge(sources=[_src(), b_src])
        a.update(b)
        agg_sources = [s for s in a.sources if s.resource_id == "infores:agg"]
        assert len(agg_sources) == 1
        assert agg_sources[0].upstream_resource_ids is not None
        assert set(agg_sources[0].upstream_resource_ids) == {
            "infores:up1",
            "infores:up2",
        }


class TestEdgeMeetsConstraints:
    def test_attribute_constraints(self):
        e = _edge(attributes=[Attribute(attribute_type_id="biolink:foo", value=1)])
        c = AttributeConstraint(id="biolink:foo", name="foo", operator="==", value=1)
        assert e.meets_attribute_constraints([c]) is True

    def test_empty_qualifier_constraints_returns_true(self):
        e = _edge()
        assert e.meets_qualifier_constraints([]) is True

    def test_qualifier_constraints_with_no_qualifiers_returns_false(self):
        e = _edge()
        # A QualifierSetConstraint is a {type_id: value} mapping.
        c = {"biolink:subject_aspect_qualifier": "activity"}
        assert e.meets_qualifier_constraints([c]) is False

    def test_qualifier_constraint_satisfied(self):
        q = Qualifier(
            qualifier_type_id="biolink:subject_aspect_qualifier",
            qualifier_value="activity",
        )
        e = _edge(qualifiers=[q])
        c = {"biolink:subject_aspect_qualifier": "activity"}
        assert e.meets_qualifier_constraints([c]) is True


class TestAppendAggregator:
    def test_appends_aggregator_with_upstream(self):
        e = _edge()  # has only a primary source
        e.append_aggregator("infores:agg")
        assert len(e.sources) == 2
        agg = e.sources[-1]
        assert agg.resource_id == "infores:agg"
        assert agg.resource_role == "aggregator_knowledge_source"
        assert agg.upstream_resource_ids == ["infores:foo"]

    def test_raises_when_chain_invalid(self):
        # No source can be the "last downstream" if every source is upstream of
        # something else. Build a cycle so last_downstream_source returns None.
        e = Edge(
            predicate="biolink:related_to",
            subject="A:1",
            object="B:2",
            sources=[
                _src(
                    "infores:a",
                    "aggregator_knowledge_source",
                    upstream=["infores:b"],
                ),
                _src(
                    "infores:b",
                    "aggregator_knowledge_source",
                    upstream=["infores:a"],
                ),
            ],
            knowledge_level="knowledge_assertion",
            agent_type="manual_agent",
        )
        with pytest.raises(ValueError, match="Provenance chain is invalid"):
            e.append_aggregator("infores:new")
