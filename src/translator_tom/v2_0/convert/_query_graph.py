"""Transforms for the QueryGraph family (Base/Pathfinder collapse) and QEdge/QPath."""

from __future__ import annotations

from typing import Any

from translator_tom.v1_6.models.query_graph import BaseQueryGraph as V16BaseQueryGraph
from translator_tom.v1_6.models.query_graph import (
    PathfinderQueryGraph as V16PathfinderQueryGraph,
)
from translator_tom.v1_6.models.query_graph import QEdge as V16QEdge
from translator_tom.v1_6.models.query_graph import QPath as V16QPath
from translator_tom.v1_6.models.query_graph import QueryGraph as V16QueryGraph
from translator_tom.v2_0.convert._path_constraint import _upgrade_path_constraint
from translator_tom.v2_0.convert._qualifier import _upgrade_qualifier_constraint
from translator_tom.v2_0.convert._util import register
from translator_tom.v2_0.models.query_graph import QEdge, QPath, QueryGraph


@register(V16QEdge, QEdge)
def _upgrade_qedge(data: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Fold attribute_constraints/qualifier_constraints into a QEdgeConstraints object.

    Each 1.6 QualifierConstraint (`qualifier_set` list) becomes a
    `{qualifier_type_id: qualifier_value}` mapping (a QualifierSetConstraint).
    """
    data = dict(data)

    attribute_constraints = data.pop("attribute_constraints", None)
    qualifier_constraints = data.pop("qualifier_constraints", None)

    constraints: dict[str, Any] = {}
    if attribute_constraints:
        constraints["attributes"] = attribute_constraints

    qualifier_sets = [
        _upgrade_qualifier_constraint(constraint, **kwargs)
        for constraint in (qualifier_constraints or [])
        if constraint.get("qualifier_set")
    ]
    if qualifier_sets:
        constraints["qualifiers"] = qualifier_sets

    if constraints:
        data["constraints"] = constraints

    return data


@register(V16QPath, QPath)
def _upgrade_qpath(data: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Convert each PathConstraint (intermediate_categories rename)."""
    data = dict(data)

    constraints = data.get("constraints")
    if constraints:
        data["constraints"] = [
            _upgrade_path_constraint(constraint, **kwargs) for constraint in constraints
        ]
    else:
        data.pop("constraints", None)

    return data


@register(V16BaseQueryGraph, QueryGraph)
@register(V16QueryGraph, QueryGraph)
@register(V16PathfinderQueryGraph, QueryGraph)
def _upgrade_query_graph(data: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Base/regular/pathfinder → the unified QueryGraph; convert QEdges and/or QPaths."""
    data = dict(data)

    edges = data.get("edges")
    if edges:
        data["edges"] = {
            qedge_id: _upgrade_qedge(qedge, **kwargs)
            for qedge_id, qedge in edges.items()
        }
    else:
        data.pop("edges", None)

    paths = data.get("paths")
    if paths:
        data["paths"] = {
            qpath_id: _upgrade_qpath(qpath, **kwargs)
            for qpath_id, qpath in paths.items()
        }
    else:
        data.pop("paths", None)

    return data
