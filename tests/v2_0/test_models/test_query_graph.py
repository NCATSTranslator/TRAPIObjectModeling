"""Tests for translator_tom.v2_0.models.query_graph."""

import pytest
from pydantic import ValidationError

from translator_tom import (
    AttributeConstraint,
    PathConstraint,
    QEdge,
    QEdgeConstraints,
    QNode,
    QPath,
    QueryGraph,
    SetInterpretationEnum,
)

# ============================================================================
# QueryGraph (single collapsed type; edges and paths are both optional)
# ============================================================================


class TestQueryGraph:
    def test_basic_nodes_only(self):
        qg = QueryGraph(nodes={"n1": QNode()})
        assert "n1" in qg.nodes
        assert qg.edges is None
        assert qg.paths is None

    def test_with_edges(self):
        qg = QueryGraph(
            nodes={"n1": QNode(), "n2": QNode()},
            edges={"e1": QEdge(subject="n1", object="n2")},
        )
        assert qg.edges is not None
        assert "e1" in qg.edges

    def test_with_paths(self):
        qg = QueryGraph(
            nodes={"n1": QNode(), "n2": QNode()},
            paths={"p1": QPath(subject="n1", object="n2")},
        )
        assert qg.paths is not None
        assert "p1" in qg.paths

    def test_nodes_min_length(self):
        with pytest.raises(ValidationError):
            QueryGraph(nodes={})

    def test_edges_min_length_when_present(self):
        with pytest.raises(ValidationError):
            QueryGraph(nodes={"n1": QNode()}, edges={})

    def test_paths_min_length_when_present(self):
        with pytest.raises(ValidationError):
            QueryGraph(nodes={"n1": QNode()}, paths={})

    def test_paths_max_length_enforced(self):
        with pytest.raises(ValidationError):
            QueryGraph(
                nodes={"n1": QNode(), "n2": QNode()},
                paths={
                    "p1": QPath(subject="n1", object="n2"),
                    "p2": QPath(subject="n1", object="n2"),
                },
            )

    def test_dict_properties_when_none(self):
        qg = QueryGraph(nodes={"n1": QNode()})
        assert qg.edges_dict == {}
        assert qg.paths_dict == {}

    def test_new_is_empty(self):
        qg = QueryGraph.new()
        assert qg.nodes == {}


# ============================================================================
# SetInterpretationEnum
# ============================================================================


class TestSetInterpretationEnum:
    @pytest.mark.parametrize(
        ("member", "value"),
        [
            (SetInterpretationEnum.BATCH, "BATCH"),
            (SetInterpretationEnum.MANY, "MANY"),
            (SetInterpretationEnum.ALL, "ALL"),
            (SetInterpretationEnum.COLLATE, "COLLATE"),
        ],
    )
    def test_values(self, member: SetInterpretationEnum, value: str):
        assert member.value == value
        assert member == value


# ============================================================================
# QNode
# ============================================================================


class TestQNode:
    def test_default_construction(self):
        q = QNode()
        assert q.ids is None
        assert q.categories is None
        assert q.set_interpretation is None
        assert q.member_ids is None
        assert q.constraints is None

    def test_ids_min_length(self):
        with pytest.raises(ValidationError):
            QNode(ids=[])

    def test_categories_min_length(self):
        with pytest.raises(ValidationError):
            QNode(categories=[])


class TestQNodeListProperties:
    def test_ids_list_when_none(self):
        assert QNode().ids_list == []

    def test_ids_list_when_set(self):
        assert QNode(ids=["A:1"]).ids_list == ["A:1"]

    def test_categories_list_when_none(self):
        assert QNode().categories_list == []

    def test_member_ids_list_when_none(self):
        assert QNode().member_ids_list == []

    def test_constraints_list_when_none(self):
        assert QNode().constraints_list == []


# ============================================================================
# QEdge
# ============================================================================


def _qedge(**kwargs: object) -> QEdge:
    defaults: dict[str, object] = {"subject": "n1", "object": "n2"}
    defaults.update(kwargs)
    return QEdge(**defaults)  # type: ignore[arg-type]


class TestQEdge:
    def test_required_fields(self):
        e = _qedge()
        assert e.subject == "n1"
        assert e.object == "n2"
        assert e.predicates is None
        assert e.constraints is None

    def test_predicates_min_length(self):
        with pytest.raises(ValidationError):
            _qedge(predicates=[])


class TestQEdgeListProperties:
    def test_predicates_list_when_none(self):
        assert _qedge().predicates_list == []


class TestQEdgeGetInverse:
    def test_swaps_subject_and_object(self):
        e = _qedge(predicates=["biolink:treats"])
        inv = e.get_inverse()
        assert inv.subject == "n2"
        assert inv.object == "n1"

    def test_inverts_predicates(self):
        e = _qedge(predicates=["biolink:treats"])
        inv = e.get_inverse()
        assert inv.predicates == ["biolink:treated_by"]

    def test_no_predicates_yields_none(self):
        e = _qedge()
        inv = e.get_inverse()
        assert inv.predicates is None

    def test_raises_when_predicate_uninvertible(self):
        # `biolink:has_count` has no inverse defined.
        e = _qedge(predicates=["biolink:has_count"])
        with pytest.raises(ValueError, match="Cannot invert"):
            e.get_inverse()

    def test_inverts_direction_scoped_attribute_constraints(self):
        e = _qedge(
            constraints=QEdgeConstraints(
                attributes=[
                    AttributeConstraint(
                        id="biolink:original_subject",
                        name="original subject",
                        operator="==",
                        value="X",
                    )
                ]
            )
        )
        inv = e.get_inverse()
        assert inv.constraints is not None
        assert inv.constraints.attributes is not None
        assert inv.constraints.attributes[0].id == "biolink:original_object"

    def test_direction_independent_attribute_constraints_pass_through(self):
        e = _qedge(
            constraints=QEdgeConstraints(
                attributes=[
                    AttributeConstraint(
                        id="biolink:foo", name="foo", operator="==", value=1
                    )
                ]
            )
        )
        inv = e.get_inverse()
        assert inv.constraints is not None
        assert inv.constraints.attributes is not None
        assert inv.constraints.attributes[0].id == "biolink:foo"

    def test_inverts_qualifier_constraints(self):
        e = _qedge(
            constraints=QEdgeConstraints(
                qualifiers=[{"biolink:subject_aspect_qualifier": "activity"}]
            )
        )
        inv = e.get_inverse()
        assert inv.constraints is not None
        assert inv.constraints.qualifiers is not None
        assert "biolink:object_aspect_qualifier" in inv.constraints.qualifiers[0]

    def test_preserves_knowledge_type(self):
        e = _qedge(predicates=["biolink:treats"], knowledge_type="inferred")
        inv = e.get_inverse()
        assert inv.knowledge_type == "inferred"


# ============================================================================
# QPath
# ============================================================================


class TestQPath:
    def test_required_fields(self):
        p = QPath(subject="n1", object="n2")
        assert p.subject == "n1"
        assert p.object == "n2"

    def test_predicates_min_length(self):
        with pytest.raises(ValidationError):
            QPath(subject="n1", object="n2", predicates=[])

    def test_constraints_min_length(self):
        with pytest.raises(ValidationError):
            QPath(subject="n1", object="n2", constraints=[])


class TestQPathListProperties:
    def test_predicates_list_when_none(self):
        assert QPath(subject="a", object="b").predicates_list == []

    def test_constraints_list_when_none(self):
        assert QPath(subject="a", object="b").constraints_list == []

    def test_constraints_list_when_set(self):
        c = PathConstraint(required_intermediate_categories=["biolink:Gene"])
        p = QPath(subject="a", object="b", constraints=[c])
        assert p.constraints_list == [c]
