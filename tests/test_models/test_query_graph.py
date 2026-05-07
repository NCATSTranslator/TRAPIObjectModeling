"""Tests for translator_tom.models.query_graph."""

import pytest
from pydantic import ValidationError

from translator_tom import (
    AttributeConstraint,
    PathConstraint,
    PathfinderQueryGraph,
    QEdge,
    QNode,
    QPath,
    Qualifier,
    QualifierConstraint,
    QueryGraph,
    SetInterpretationEnum,
)


# ============================================================================
# QueryGraph / PathfinderQueryGraph
# ============================================================================


class TestQueryGraph:
    def test_basic(self):
        qg = QueryGraph(nodes={"n1": QNode()}, edges={})
        assert "n1" in qg.nodes
        assert qg.edges == {}


class TestPathfinderQueryGraph:
    def test_basic(self):
        pqg = PathfinderQueryGraph(
            nodes={"n1": QNode(), "n2": QNode()},
            paths={"p1": QPath(subject="n1", object="n2")},
        )
        assert "p1" in pqg.paths

    def test_paths_min_length_enforced(self):
        with pytest.raises(ValidationError):
            PathfinderQueryGraph(nodes={}, paths={})

    def test_paths_max_length_enforced(self):
        with pytest.raises(ValidationError):
            PathfinderQueryGraph(
                nodes={"n1": QNode(), "n2": QNode()},
                paths={
                    "p1": QPath(subject="n1", object="n2"),
                    "p2": QPath(subject="n1", object="n2"),
                },
            )


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

    def test_predicates_min_length(self):
        with pytest.raises(ValidationError):
            _qedge(predicates=[])


class TestQEdgeListProperties:
    def test_predicates_list_when_none(self):
        assert _qedge().predicates_list == []

    def test_attribute_constraints_list_when_none(self):
        assert _qedge().attribute_constraints_list == []

    def test_qualifier_constraints_list_when_none(self):
        assert _qedge().qualifier_constraints_list == []


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

    def test_raises_when_attribute_constraints_present(self):
        e = _qedge(
            attribute_constraints=[
                AttributeConstraint(
                    id="biolink:foo", name="foo", operator="==", value=1
                )
            ]
        )
        with pytest.raises(NotImplementedError):
            e.get_inverse()

    def test_inverts_qualifier_constraints(self):
        q = Qualifier(
            qualifier_type_id="biolink:subject_aspect_qualifier",
            qualifier_value="activity",
        )
        e = _qedge(qualifier_constraints=[QualifierConstraint(qualifier_set=[q])])
        inv = e.get_inverse()
        assert inv.qualifier_constraints is not None
        assert (
            inv.qualifier_constraints[0].qualifier_set[0].qualifier_type_id
            == "biolink:object_aspect_qualifier"
        )

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
        c = PathConstraint(intermediate_categories=["biolink:Gene"])
        p = QPath(subject="a", object="b", constraints=[c])
        assert p.constraints_list == [c]
