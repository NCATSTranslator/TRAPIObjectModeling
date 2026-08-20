"""Tests for the `*DictUtil` sibling classes in `model_dicts/query_graph.py`.

The util classes reimplement the utility methods of the `QNode`/`QEdge`/`QPath`
Pydantic models for their `TypedDict` equivalents. Most tests assert parity with
the Pydantic behaviour by comparing against `model.get_inverse().to_dict()`.
"""

from __future__ import annotations

from typing import Annotated, Literal

import pytest
from pydantic import Field

from translator_tom.v1_6.model_dicts.attribute import AttributeConstraintDictUtil
from translator_tom.v1_6.model_dicts.qualifier import QualifierConstraintDictUtil
from translator_tom.v1_6.model_dicts.query_graph import (
    PathfinderQueryGraphDictUtil,
    QEdgeDict,
    QEdgeDictUtil,
    QNodeDict,
    QNodeDictUtil,
    QPathDict,
    QPathDictUtil,
    QueryGraphDictUtil,
)
from translator_tom.v1_6.models.attribute import AttributeConstraint
from translator_tom.v1_6.models.path_constraint import PathConstraint
from translator_tom.v1_6.models.qualifier import Qualifier, QualifierConstraint
from translator_tom.v1_6.models.query_graph import (
    PathfinderQueryGraph,
    QEdge,
    QNode,
    QPath,
    QueryGraph,
)
from translator_tom.utils.dict_util_base import DictUtil
from translator_tom.utils.object_base import TOMBase

# ============================================================================
# QNodeDictUtil — list accessors
# ============================================================================


class TestQNodeDictUtilListAccessors:
    def test_missing_keys_return_empty(self):
        qnode: QNodeDict = {}
        assert QNodeDictUtil.ids_list(qnode) == []
        assert QNodeDictUtil.categories_list(qnode) == []
        assert QNodeDictUtil.member_ids_list(qnode) == []
        assert QNodeDictUtil.constraints_list(qnode) == []

    def test_explicit_none_returns_empty(self):
        qnode: QNodeDict = {"ids": None, "categories": None}
        assert QNodeDictUtil.ids_list(qnode) == []
        assert QNodeDictUtil.categories_list(qnode) == []

    def test_populated_returns_value(self):
        qnode: QNodeDict = {
            "ids": ["CHEBI:1"],
            "categories": ["biolink:ChemicalEntity"],
        }
        assert QNodeDictUtil.ids_list(qnode) == ["CHEBI:1"]
        assert QNodeDictUtil.categories_list(qnode) == ["biolink:ChemicalEntity"]


# ============================================================================
# QEdgeDictUtil — list accessors
# ============================================================================


class TestQEdgeDictUtilListAccessors:
    def test_missing_keys_return_empty(self):
        qedge: QEdgeDict = {"subject": "n0", "object": "n1"}
        assert QEdgeDictUtil.predicates_list(qedge) == []
        assert QEdgeDictUtil.attribute_constraints_list(qedge) == []
        assert QEdgeDictUtil.qualifier_constraints_list(qedge) == []

    def test_populated_returns_value(self):
        qedge: QEdgeDict = {
            "subject": "n0",
            "object": "n1",
            "predicates": ["biolink:treats"],
        }
        assert QEdgeDictUtil.predicates_list(qedge) == ["biolink:treats"]


# ============================================================================
# QEdgeDictUtil.get_inverse — parity with QEdge.get_inverse
# ============================================================================


def _assert_inverse_parity(edge: QEdge) -> None:
    """The dict util inverse should match the model's serialized inverse exactly."""
    edge_dict = edge.to_dict()
    assert QEdgeDictUtil.get_inverse(edge_dict) == edge.get_inverse().to_dict()


class TestQEdgeDictUtilGetInverse:
    def test_swaps_subject_and_object(self):
        qedge: QEdgeDict = {"subject": "n0", "object": "n1"}
        inverted = QEdgeDictUtil.get_inverse(qedge)
        assert inverted["subject"] == "n1"
        assert inverted["object"] == "n0"

    def test_inverts_predicates(self):
        qedge: QEdgeDict = {
            "subject": "n0",
            "object": "n1",
            "predicates": ["biolink:treats"],
        }
        assert QEdgeDictUtil.get_inverse(qedge)["predicates"] == ["biolink:treated_by"]

    def test_no_predicates_key_omitted(self):
        qedge: QEdgeDict = {"subject": "n0", "object": "n1"}
        assert "predicates" not in QEdgeDictUtil.get_inverse(qedge)

    def test_raises_when_predicate_uninvertible(self):
        qedge: QEdgeDict = {
            "subject": "n0",
            "object": "n1",
            "predicates": ["biolink:has_count"],
        }
        with pytest.raises(ValueError, match="Cannot invert predicates"):
            QEdgeDictUtil.get_inverse(qedge)

    def test_parity_predicates(self):
        _assert_inverse_parity(
            QEdge(subject="n0", object="n1", predicates=["biolink:treats"])
        )

    def test_parity_knowledge_type(self):
        _assert_inverse_parity(
            QEdge(
                subject="n0",
                object="n1",
                predicates=["biolink:treats"],
                knowledge_type="inferred",
            )
        )

    def test_parity_direction_scoped_attribute_constraints(self):
        _assert_inverse_parity(
            QEdge(
                subject="n0",
                object="n1",
                attribute_constraints=[
                    AttributeConstraint(
                        id="biolink:original_subject",
                        name="original subject",
                        operator="==",
                        value="X",
                    )
                ],
            )
        )

    def test_parity_qualifier_constraints(self):
        _assert_inverse_parity(
            QEdge(
                subject="n0",
                object="n1",
                qualifier_constraints=[
                    QualifierConstraint(
                        qualifier_set=[
                            Qualifier(
                                qualifier_type_id="biolink:subject_aspect_qualifier",
                                qualifier_value="activity",
                            )
                        ]
                    )
                ],
            )
        )


# ============================================================================
# QPathDictUtil — list accessors
# ============================================================================


class TestQPathDictUtilListAccessors:
    def test_missing_keys_return_empty(self):
        qpath: QPathDict = {"subject": "n0", "object": "n1"}
        assert QPathDictUtil.predicates_list(qpath) == []
        assert QPathDictUtil.constraints_list(qpath) == []

    def test_populated_returns_value(self):
        qpath: QPathDict = {
            "subject": "n0",
            "object": "n1",
            "predicates": ["biolink:related_to"],
        }
        assert QPathDictUtil.predicates_list(qpath) == ["biolink:related_to"]


# ============================================================================
# hash — parity with the model's hash(), including nested-model recursion
# ============================================================================


class TestHashParity:
    def test_qnode_empty(self):
        node = QNode()
        assert QNodeDictUtil.hash(node.to_dict()) == node.hash()

    def test_qnode_scalar_fields(self):
        node = QNode(ids=["CHEBI:1"], categories=["biolink:ChemicalEntity"])
        assert QNodeDictUtil.hash(node.to_dict()) == node.hash()

    def test_qnode_with_nested_attribute_constraints(self):
        node = QNode(
            ids=["CHEBI:1"],
            constraints=[
                AttributeConstraint(
                    id="biolink:x", name="x", operator="==", value=[1, 2]
                )
            ],
        )
        assert QNodeDictUtil.hash(node.to_dict()) == node.hash()

    def test_qedge_with_all_nested_constraints(self):
        edge = QEdge(
            subject="n0",
            object="n1",
            predicates=["biolink:treats"],
            attribute_constraints=[
                AttributeConstraint(id="biolink:x", name="x", operator="==", value=1)
            ],
            qualifier_constraints=[
                QualifierConstraint(
                    qualifier_set=[
                        Qualifier(
                            qualifier_type_id="biolink:subject_aspect_qualifier",
                            qualifier_value="activity",
                        )
                    ]
                )
            ],
        )
        assert QEdgeDictUtil.hash(edge.to_dict()) == edge.hash()

    def test_qpath_with_nested_path_constraints(self):
        path = QPath(
            subject="n0",
            object="n1",
            constraints=[
                PathConstraint(intermediate_categories=["biolink:Gene"]),
            ],
        )
        assert QPathDictUtil.hash(path.to_dict()) == path.hash()

    def test_hash_ignores_extra_keys(self):
        node = QNode(ids=["CHEBI:1"])
        with_extra = {**node.to_dict(), "unexpected": "ignored"}
        assert QNodeDictUtil.hash(with_extra) == node.hash()


# ============================================================================
# I/O — JSON / MessagePack round-trips and model interop
# ============================================================================


class TestIO:
    def test_json_roundtrip(self):
        qedge: QEdgeDict = {
            "subject": "n0",
            "object": "n1",
            "predicates": ["biolink:treats"],
        }
        assert QEdgeDictUtil.from_json(QEdgeDictUtil.to_json(qedge)) == qedge

    def test_to_json_as_str(self):
        qedge: QEdgeDict = {"subject": "n0", "object": "n1"}
        assert isinstance(QEdgeDictUtil.to_json(qedge, as_str=True), str)
        assert isinstance(QEdgeDictUtil.to_json(qedge), bytes)

    def test_msgpack_roundtrip(self):
        qedge: QEdgeDict = {
            "subject": "n0",
            "object": "n1",
            "predicates": ["biolink:treats"],
        }
        assert QEdgeDictUtil.from_msgpack(QEdgeDictUtil.to_msgpack(qedge)) == qedge

    def test_from_model_json_interop(self):
        edge = QEdge(subject="n0", object="n1", predicates=["biolink:treats"])
        assert QEdgeDictUtil.from_json(edge.to_json()) == edge.to_dict()


# ============================================================================
# Nested-util derivation (auto-derived from the model's field types)
# ============================================================================


class _Inner(TOMBase):
    x: int = 0


class _Outer(TOMBase):
    inner: _Inner | None = None


class _OuterDictUtil(DictUtil[dict[str, object]]):
    """A util whose model nests `_Inner`, which deliberately has no util."""

    _model = _Outer


class TestNestedDerivation:
    def test_derived_mapping(self):
        # Each entry is a value-hasher mirroring the field's container shape and
        # routing element dicts through the resolved member util.
        ac = {"id": "biolink:x", "name": "n", "operator": "==", "value": 1}
        qc = {"qualifier_set": [{"qualifier_type_id": "biolink:x", "qualifier_value": "y"}]}
        qnode = QNodeDictUtil._nested_fields()
        assert set(qnode) == {"constraints"}
        assert qnode["constraints"]([ac]) == [AttributeConstraintDictUtil.hash(ac)]
        qedge = QEdgeDictUtil._nested_fields()
        assert set(qedge) == {"attribute_constraints", "qualifier_constraints"}
        assert qedge["attribute_constraints"]([ac]) == [AttributeConstraintDictUtil.hash(ac)]
        assert qedge["qualifier_constraints"]([qc]) == [QualifierConstraintDictUtil.hash(qc)]

    def test_scalar_only_model_has_empty_mapping(self):
        # AttributeConstraintDictUtil overrides hash, but base derivation still
        # yields nothing since AttributeConstraint has no nested-model fields.
        assert AttributeConstraintDictUtil._nested_fields() == {}

    def test_missing_nested_util_raises_loudly(self):
        with pytest.raises(LookupError, match="_InnerDictUtil"):
            _OuterDictUtil.hash({"inner": {"x": 1}})


# ============================================================================
# Deeply-nested containers (dict-of-lists, list-of-lists, set/tuple leaves)
# ============================================================================


class _Leaf(TOMBase):
    x: int = 0


class _LeafDictUtil(DictUtil[dict[str, object]]):
    _model = _Leaf


class _Nested(TOMBase):
    dl: dict[str, list[_Leaf]] | None = None  # dict of lists of models
    ll: list[list[_Leaf]] | None = None  # list of lists of models
    tup: tuple[_Leaf, ...] | None = None  # tuple leaf (container kind preserved)


class _NestedDictUtil(DictUtil[dict[str, object]]):
    _model = _Nested


class TestDeeplyNestedContainerHashing:
    """The value-hasher must recurse through *nested* containers, not just the
    outermost one, and preserve each container's kind for parity.
    """

    def test_dict_of_lists_and_list_of_lists_parity(self):
        m = _Nested(
            dl={"a": [_Leaf(x=1), _Leaf(x=2)], "b": [_Leaf(x=3)]},
            ll=[[_Leaf(x=4)], [_Leaf(x=5), _Leaf(x=6)]],
            tup=(_Leaf(x=7), _Leaf(x=8)),
        )
        assert _NestedDictUtil.hash(m.to_dict()) == m.hash()

    def test_empty_nested_containers_parity(self):
        m = _Nested(dl={}, ll=[])
        assert _NestedDictUtil.hash(m.to_dict()) == m.hash()


# ============================================================================
# Union nested fields (discriminator-aware resolution)
# ============================================================================

# A model with a structural (non-tagged) union field: `QueryGraph | PathfinderQueryGraph`
# mirrors `Message.query_graph`, resolved via the registered structural discriminator.


class _QGHolder(TOMBase):
    query_graph: QueryGraph | PathfinderQueryGraph | None = None


class _QGHolderDictUtil(DictUtil[dict[str, object]]):
    _model = _QGHolder


# A model with a pydantic tagged union field (discriminated by `kind`), mirroring the
# `Annotated[..., Field(discriminator=...)]` shape of TRAPI's `workflow`.


# The discriminator is required (no default), as in real TRAPI tagged unions
# (Operation.id) — so exclude_defaults never drops the key the resolver needs.
class _Cat(TOMBase):
    kind: Literal["cat"]
    meow: int = 1


class _Dog(TOMBase):
    kind: Literal["dog"]
    woof: int = 2


_Pet = Annotated[_Cat | _Dog, Field(discriminator="kind")]


class _PetHolder(TOMBase):
    pets: list[_Pet] | None = None


class _CatDictUtil(DictUtil[dict[str, object]]):
    _model = _Cat


class _DogDictUtil(DictUtil[dict[str, object]]):
    _model = _Dog


class _PetHolderDictUtil(DictUtil[dict[str, object]]):
    _model = _PetHolder


class TestUnionHashParity:
    def test_query_graph_members_hash(self):
        qg = QueryGraph(
            nodes={"n0": QNode(ids=["CHEBI:1"])},
            edges={"e0": QEdge(subject="n0", object="n1", predicates=["biolink:treats"])},
        )
        assert QueryGraphDictUtil.hash(qg.to_dict()) == qg.hash()
        pqg = PathfinderQueryGraph(
            nodes={"n0": QNode(ids=["CHEBI:1"])},
            paths={"p0": QPath(subject="n0", object="n1")},
        )
        assert PathfinderQueryGraphDictUtil.hash(pqg.to_dict()) == pqg.hash()

    def test_structural_union_end_to_end(self):
        # Uses the real registered `QueryGraph | PathfinderQueryGraph` discriminator.
        for qg in (
            QueryGraph(nodes={"n0": QNode()}, edges={}),
            PathfinderQueryGraph(
                nodes={"n0": QNode()}, paths={"p0": QPath(subject="n0", object="n1")}
            ),
        ):
            holder = _QGHolder(query_graph=qg)
            assert _QGHolderDictUtil.hash(holder.to_dict()) == holder.hash()

    def test_tagged_union_end_to_end(self):
        holder = _PetHolder(pets=[_Cat(kind="cat", meow=3), _Dog(kind="dog", woof=4)])
        assert _PetHolderDictUtil.hash(holder.to_dict()) == holder.hash()

    def test_tagged_union_resolver_picks_by_tag(self):
        pets = _PetHolderDictUtil._nested_fields()["pets"]
        cat = {"kind": "cat", "meow": 3}
        dog = {"kind": "dog", "woof": 4}
        # list-hasher routes each element to the util matching its tag
        assert pets([cat, dog]) == [_CatDictUtil.hash(cat), _DogDictUtil.hash(dog)]


class _UnregisteredA(TOMBase):
    a: int = 0


class _UnregisteredB(TOMBase):
    b: int = 0


class _UnregisteredHolder(TOMBase):
    item: _UnregisteredA | _UnregisteredB | None = None


class _UnregisteredHolderDictUtil(DictUtil[dict[str, object]]):
    _model = _UnregisteredHolder


class _UnregisteredADictUtil(DictUtil[dict[str, object]]):
    _model = _UnregisteredA


class _UnregisteredBDictUtil(DictUtil[dict[str, object]]):
    _model = _UnregisteredB


def test_unregistered_structural_union_raises_loudly():
    # Utils exist for both members, but no discriminator is registered for the union.
    with pytest.raises(LookupError, match="no discriminator"):
        _UnregisteredHolderDictUtil.hash({"item": {"a": 1}})
