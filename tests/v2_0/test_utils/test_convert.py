import inspect

from translator_tom import up_version, v1_6, v2_0
from translator_tom.model_dicts import dict_up_version
from translator_tom.utils.object_base import TOMBase
from translator_tom.v2_0._version import SCHEMA_VERSION
from translator_tom.v2_0.convert._util import _TRANSFORMS
from translator_tom.v2_0.validation import passes_semantic_validation

# --- 1.6 factory helpers -----------------------------------------------------------


def _src() -> v1_6.RetrievalSource:
    return v1_6.RetrievalSource(
        resource_id="infores:foo",
        resource_role="primary_knowledge_source",
    )


def _kl_attr(value: str = "knowledge_assertion") -> v1_6.Attribute:
    return v1_6.Attribute(attribute_type_id="biolink:knowledge_level", value=value)


def _at_attr(value: str = "manual_agent") -> v1_6.Attribute:
    return v1_6.Attribute(attribute_type_id="biolink:agent_type", value=value)


def _edge(*, with_kl_at: bool = True) -> v1_6.Edge:
    attributes = [
        v1_6.Attribute(attribute_type_id="biolink:publications", value=["PMID:1"])
    ]
    if with_kl_at:
        attributes = [_kl_attr(), _at_attr(), *attributes]
    return v1_6.Edge(
        predicate="biolink:related_to",
        subject="NCBIGene:1",
        object="MONDO:1",
        sources=[_src()],
        attributes=attributes,
    )


def _kg() -> v1_6.KnowledgeGraph:
    return v1_6.KnowledgeGraph(
        nodes={
            "NCBIGene:1": v1_6.Node(categories=["biolink:Gene"], attributes=[]),
            "MONDO:1": v1_6.Node(categories=["biolink:Disease"], attributes=[]),
        },
        edges={"e0": _edge()},
    )


def _result() -> v1_6.Result:
    analysis = v1_6.Analysis(
        resource_id="infores:ara",
        edge_bindings={
            "qe0": [
                v1_6.EdgeBinding(id="e0", attributes=[]),
                v1_6.EdgeBinding(id="e0", attributes=[]),  # duplicate → single id
            ]
        },
    )
    return v1_6.Result(
        node_bindings={
            "qn0": [
                v1_6.NodeBinding(id="NCBIGene:1", attributes=[]),
                v1_6.NodeBinding(
                    id="NCBIGene:1", attributes=[]
                ),  # duplicate → single id
            ],
            "qn1": [v1_6.NodeBinding(id="MONDO:1", attributes=[])],
        },
        analyses=[analysis],
    )


# --- Edge: KL/AT lift --------------------------------------------------------------


def test_edge_lifts_knowledge_level_and_agent_type():
    out = up_version(_edge())
    assert isinstance(out, v2_0.Edge)
    assert out.knowledge_level == "knowledge_assertion"
    assert out.agent_type == "manual_agent"
    # the two lifted attributes are removed; the rest remain
    assert [a.attribute_type_id for a in out.attributes_list] == [
        "biolink:publications"
    ]


def test_edge_defaults_missing_kl_at_to_not_provided():
    out = up_version(_edge(with_kl_at=False))
    assert out.knowledge_level == "not_provided"
    assert out.agent_type == "not_provided"


# --- bindings: list → single object with ids ---------------------------------------


def test_node_bindings_collapse_and_dedup():
    out = up_version(_result())
    assert out.node_bindings["qn0"].ids == ["NCBIGene:1"]
    assert out.node_bindings["qn1"].ids == ["MONDO:1"]


def test_edge_bindings_collapse_and_dedup():
    out = up_version(_result())
    assert out.analyses[0].edge_bindings["qe0"].ids == ["e0"]


def test_standalone_binding_converts():
    assert up_version(v1_6.NodeBinding(id="X:1", attributes=[])).ids == ["X:1"]
    assert up_version(v1_6.PathBinding(id="aux0")).ids == ["aux0"]


# --- Pathfinder collapse -----------------------------------------------------------


def test_pathfinder_query_graph_collapses_to_query_graph():
    pfqg = v1_6.PathfinderQueryGraph(
        nodes={"a": v1_6.QNode(ids=["CHEBI:1"]), "b": v1_6.QNode(ids=["MONDO:1"])},
        paths={
            "p0": v1_6.QPath(
                subject="a",
                object="b",
                constraints=[
                    v1_6.PathConstraint(intermediate_categories=["biolink:Gene"])
                ],
            )
        },
    )
    out = up_version(pfqg)
    assert isinstance(out, v2_0.QueryGraph)
    assert out.edges is None
    assert list(out.paths) == ["p0"]
    # PathConstraint field rename
    assert out.paths["p0"].constraints[0].required_intermediate_categories == [
        "biolink:Gene"
    ]


def test_pathfinder_analysis_collapses_to_analysis():
    pfa = v1_6.PathfinderAnalysis(
        resource_id="infores:pf",
        path_bindings={"p0": [v1_6.PathBinding(id="aux0")]},
    )
    out = up_version(pfa)
    assert isinstance(out, v2_0.Analysis)
    assert out.edge_bindings is None
    assert out.path_bindings["p0"].ids == ["aux0"]


# --- QEdge constraints refactor ----------------------------------------------------


def test_qedge_constraints_fold_and_qualifier_reshape():
    qe = v1_6.QEdge(
        subject="a",
        object="b",
        attribute_constraints=[
            v1_6.AttributeConstraint(id="biolink:x", name="x", operator="==", value=1)
        ],
        qualifier_constraints=[
            v1_6.QualifierConstraint(
                qualifier_set=[
                    v1_6.Qualifier(
                        qualifier_type_id="biolink:object_aspect_qualifier",
                        qualifier_value="expression",
                    )
                ]
            )
        ],
    )
    out = up_version(qe)
    assert [a.id for a in out.constraints.attributes] == ["biolink:x"]
    assert out.constraints.qualifiers == [
        {"biolink:object_aspect_qualifier": "expression"}
    ]


def test_standalone_qualifier_constraint_becomes_mapping():
    qc = v1_6.QualifierConstraint(
        qualifier_set=[
            v1_6.Qualifier(
                qualifier_type_id="biolink:object_aspect_qualifier",
                qualifier_value="expression",
            )
        ]
    )
    assert up_version(qc) == {"biolink:object_aspect_qualifier": "expression"}


# --- Query / Response --------------------------------------------------------------


def test_query_moves_params_under_parameters():
    q = v1_6.Query(message=v1_6.Message(), log_level="DEBUG", bypass_cache=True)
    out = up_version(q)
    assert out.parameters.log_level == "DEBUG"
    assert out.parameters.bypass_cache is True


def test_async_query_type_and_callback_preserved():
    aq = v1_6.AsyncQuery(
        message=v1_6.Message(), callback="http://cb", log_level="ERROR"
    )
    out = up_version(aq)
    assert isinstance(out, v2_0.AsyncQuery)
    assert out.callback == "http://cb"
    assert out.parameters.log_level == "ERROR"


def test_response_drops_empty_logs_and_restamps_schema_version():
    resp = v1_6.Response(
        message=v1_6.Message(knowledge_graph=_kg()), logs=[], schema_version="1.6.0"
    )
    out = up_version(resp)
    assert out.logs is None
    assert out.schema_version == SCHEMA_VERSION


# --- AuxiliaryGraph ----------------------------------------------------------------


def test_auxiliary_graph_drops_attributes():
    ag = v1_6.AuxiliaryGraph(
        edges=["e0"],
        attributes=[v1_6.Attribute(attribute_type_id="biolink:x", value=1)],
    )
    out = up_version(ag)
    assert "attributes" not in out.to_dict()
    assert out.edges == ["e0"]


# --- full-tree round trip ----------------------------------------------------------


def test_full_response_round_trip_passes_semantic_validation():
    resp = v1_6.Response(
        message=v1_6.Message(knowledge_graph=_kg(), results=[_result()]),
        logs=[],
        schema_version="1.6.0",
    )
    out = up_version(resp)
    assert isinstance(out, v2_0.Response)
    assert passes_semantic_validation(out)


# --- empty-array normalization (2.0 forbids empty minItems:1 arrays) ---------------


def test_optional_empty_arrays_dropped_to_absent():
    edge = v1_6.Edge(
        predicate="biolink:related_to",
        subject="A:1",
        object="B:2",
        sources=[_src()],
        attributes=[_kl_attr(), _at_attr()],
        qualifiers=[],
    )
    assert up_version(edge).qualifiers is None

    qnode = up_version(v1_6.QNode(ids=["X:1"], member_ids=[], constraints=[]))
    assert qnode.member_ids is None
    assert qnode.constraints is None

    analysis = v1_6.Analysis(
        resource_id="infores:ara",
        edge_bindings={"qe0": [v1_6.EdgeBinding(id="e0", attributes=[])]},
        support_graphs=[],
    )
    assert up_version(analysis).support_graphs is None

    source = v1_6.RetrievalSource(
        resource_id="infores:x",
        resource_role="aggregator_knowledge_source",
        upstream_resource_ids=[],
    )
    assert up_version(source).upstream_resource_ids is None


def test_deeply_nested_empty_array_dropped():
    # A MetaEdge with empty qualifiers, nested inside a pass-through MetaKnowledgeGraph.
    metakg = v1_6.MetaKnowledgeGraph(
        nodes={"biolink:Gene": v1_6.MetaNode(id_prefixes=["NCBIGene"])},
        edges=[
            v1_6.MetaEdge(
                subject="biolink:Gene",
                predicate="biolink:related_to",
                object="biolink:Disease",
                qualifiers=[],
            )
        ],
    )
    out = up_version(metakg)
    assert out.edges[0].qualifiers is None


def test_required_empty_value_preserved():
    # `Attribute.value` is required; a genuinely empty-list value must NOT be pruned.
    attr = v1_6.Attribute(attribute_type_id="biolink:xref", value=[])
    assert up_version(attr).value == []


def test_empty_knowledge_graph_nodes_preserved():
    # KnowledgeGraph.nodes is required (empty object allowed in 2.0); keep it, while
    # empty edges become absent.
    out = up_version(v1_6.KnowledgeGraph(nodes={}, edges={}))
    assert out.nodes == {}
    assert out.edges is None


# --- completeness sweep ------------------------------------------------------------


def test_every_v1_6_model_is_convertible():
    """Guard the passthrough default: each 1.6 model is registered or has a 2.0 twin."""
    gaps = []
    for name in v1_6.__all__:
        obj = getattr(v1_6, name)
        if inspect.isclass(obj) and issubclass(obj, TOMBase):
            registered = obj in _TRANSFORMS
            has_twin = getattr(v2_0, name, None) is not None
            if not (registered or has_twin):
                gaps.append(name)
    assert gaps == []


# --- dict-layer up_version (shared transform; parity with the model layer) ---------


def _upgraded_dict(model: TOMBase) -> object:
    """The model layer's upgrade as a dict (QualifierConstraint upgrades to a mapping)."""
    result = up_version(model)
    return result.to_dict() if isinstance(result, TOMBase) else result


def _pathfinder_query_graph() -> v1_6.PathfinderQueryGraph:
    return v1_6.PathfinderQueryGraph(
        nodes={"a": v1_6.QNode(ids=["CHEBI:1"]), "b": v1_6.QNode(ids=["MONDO:1"])},
        paths={
            "p0": v1_6.QPath(
                subject="a",
                object="b",
                constraints=[
                    v1_6.PathConstraint(intermediate_categories=["biolink:Gene"])
                ],
            )
        },
    )


def _qedge() -> v1_6.QEdge:
    return v1_6.QEdge(
        subject="a",
        object="b",
        attribute_constraints=[
            v1_6.AttributeConstraint(id="biolink:x", name="x", operator="==", value=1)
        ],
        qualifier_constraints=[
            v1_6.QualifierConstraint(
                qualifier_set=[
                    v1_6.Qualifier(
                        qualifier_type_id="biolink:object_aspect_qualifier",
                        qualifier_value="expression",
                    )
                ]
            )
        ],
    )


def test_dict_matches_model_layer_across_shapes():
    # Each layer shares the same transform, so the dict path must equal the model path.
    models: list[TOMBase] = [
        _edge(),
        _edge(with_kl_at=False),
        _kg(),
        _result(),
        _qedge(),
        _pathfinder_query_graph(),
        v1_6.AuxiliaryGraph(
            edges=["e0"],
            attributes=[v1_6.Attribute(attribute_type_id="biolink:x", value=1)],
        ),
        v1_6.Query(message=v1_6.Message(), log_level="DEBUG", bypass_cache=True),
        v1_6.AsyncQuery(
            message=v1_6.Message(), callback="http://cb", log_level="ERROR"
        ),
        v1_6.Response(
            message=v1_6.Message(knowledge_graph=_kg(), results=[_result()]),
            logs=[],
            schema_version="1.6.0",
        ),
    ]
    for model in models:
        assert dict_up_version(model.to_dict(), type(model)) == _upgraded_dict(model), (
            type(model).__name__
        )


def test_dict_result_is_valid_2_0():
    resp = v1_6.Response(
        message=v1_6.Message(knowledge_graph=_kg(), results=[_result()]),
        schema_version="1.6.0",
    )
    result = dict_up_version(resp.to_dict(), v1_6.Response)
    assert passes_semantic_validation(v2_0.Response.from_dict(result))


def _has_null(obj: object) -> bool:
    if isinstance(obj, dict):
        return any(value is None or _has_null(value) for value in obj.values())
    if isinstance(obj, list):
        return any(_has_null(item) for item in obj)
    return False


def test_dict_strips_nulls_from_raw_input():
    # A raw 1.6 dict (unlike model.to_dict()) still carries null-valued optional fields;
    # 2.0 forbids null, so dict_up_version must drop them (like to_dict's exclude_none).
    raw = v1_6.Response(message=v1_6.Message(knowledge_graph=_kg())).to_dict()
    attribute = raw["message"]["knowledge_graph"]["edges"]["e0"]["attributes"][-1]
    attribute["value_type_id"] = None
    attribute["description"] = None
    assert _has_null(raw)  # the input now carries nulls

    assert not _has_null(dict_up_version(raw, v1_6.Response))


def _raw_edge(attributes: object) -> dict:
    return {
        "predicate": "biolink:related_to",
        "subject": "A:1",
        "object": "B:2",
        "sources": [
            {"resource_id": "infores:foo", "resource_role": "primary_knowledge_source"}
        ],
        "attributes": attributes,
    }


def test_dict_edge_tolerates_null_attributes():
    # A raw 1.6 edge may carry `attributes: null` (valid 1.6); the transform must not
    # choke on it, and KL/AT fall back to the default.
    out = dict_up_version(_raw_edge(None), v1_6.Edge)
    assert out["knowledge_level"] == "not_provided"
    assert out["agent_type"] == "not_provided"


def test_dict_edge_null_kl_value_falls_back_to_default():
    # A KL attribute whose value is null must default (not become a pruned-away null,
    # which would leave the required 2.0 field missing).
    out = dict_up_version(
        _raw_edge(
            [
                {"attribute_type_id": "biolink:knowledge_level", "value": None},
                {"attribute_type_id": "biolink:agent_type", "value": "manual_agent"},
            ]
        ),
        v1_6.Edge,
    )
    assert out["knowledge_level"] == "not_provided"
    assert out["agent_type"] == "manual_agent"
    assert passes_semantic_validation(v2_0.Edge.from_dict(out))
