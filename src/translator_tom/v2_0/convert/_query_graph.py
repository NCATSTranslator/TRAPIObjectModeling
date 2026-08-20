"""Converters for the QueryGraph family (Base/Pathfinder collapse) and QEdge/QPath."""

from __future__ import annotations

from typing import Any

from translator_tom.v1_6.models.query_graph import BaseQueryGraph as V16BaseQueryGraph
from translator_tom.v1_6.models.query_graph import (
    PathfinderQueryGraph as V16PathfinderQueryGraph,
)
from translator_tom.v1_6.models.query_graph import QEdge as V16QEdge
from translator_tom.v1_6.models.query_graph import QPath as V16QPath
from translator_tom.v1_6.models.query_graph import QueryGraph as V16QueryGraph
from translator_tom.v2_0.convert._util import _build, up_version
from translator_tom.v2_0.models.query_graph import QEdge, QPath, QueryGraph


@up_version.register(V16BaseQueryGraph)
def _convert_base_query_graph(obj: V16BaseQueryGraph, **_: Any) -> QueryGraph:
    """A nodes-only QueryGraph (no edges or paths)."""
    return _build(QueryGraph, obj.to_dict())


@up_version.register(V16QueryGraph)
def _convert_query_graph(obj: V16QueryGraph, **kwargs: Any) -> QueryGraph:
    """A non-Pathfinder QueryGraph: convert each QEdge onto the unified class."""
    data = obj.to_dict()

    if obj.edges:
        data["edges"] = {
            qedge_id: up_version(qedge, **kwargs).to_dict()
            for qedge_id, qedge in obj.edges.items()
        }
    else:
        data.pop("edges", None)

    return _build(QueryGraph, data)


@up_version.register(V16PathfinderQueryGraph)
def _convert_pathfinder_query_graph(
    obj: V16PathfinderQueryGraph, **kwargs: Any
) -> QueryGraph:
    """A Pathfinder QueryGraph: convert each QPath onto the unified class."""
    data = obj.to_dict()

    data["paths"] = {
        qpath_id: up_version(qpath, **kwargs).to_dict()
        for qpath_id, qpath in obj.paths.items()
    }

    return _build(QueryGraph, data)


@up_version.register(V16QEdge)
def _convert_qedge(obj: V16QEdge, **kwargs: Any) -> QEdge:
    """Fold attribute_constraints/qualifier_constraints into a QEdgeConstraints object.

    Each 1.6 QualifierConstraint (`qualifier_set` list) becomes a
    `{qualifier_type_id: qualifier_value}` mapping (a QualifierSetConstraint).
    """
    data = obj.to_dict()
    data.pop("attribute_constraints", None)
    data.pop("qualifier_constraints", None)

    constraints: dict[str, Any] = {}
    if obj.attribute_constraints:
        constraints["attributes"] = [
            constraint.to_dict() for constraint in obj.attribute_constraints
        ]

    qualifier_sets = [
        up_version(constraint, **kwargs)
        for constraint in obj.qualifier_constraints_list
        if constraint.qualifier_set
    ]
    if qualifier_sets:
        constraints["qualifiers"] = qualifier_sets

    if constraints:
        data["constraints"] = constraints

    return _build(QEdge, data)


@up_version.register(V16QPath)
def _convert_qpath(obj: V16QPath, **kwargs: Any) -> QPath:
    """Convert each PathConstraint (intermediate_categories rename)."""
    data = obj.to_dict()

    if obj.constraints:
        data["constraints"] = [
            up_version(constraint, **kwargs).to_dict() for constraint in obj.constraints
        ]
    else:
        data.pop("constraints", None)

    return _build(QPath, data)
