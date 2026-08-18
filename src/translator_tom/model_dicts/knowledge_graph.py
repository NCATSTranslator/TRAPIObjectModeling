from __future__ import annotations

import itertools
from copy import deepcopy
from typing import Literal, cast

from typing_extensions import NotRequired, TypedDict

from translator_tom.model_dicts.analysis import AnalysisDictUtil
from translator_tom.model_dicts.attribute import (
    AttributeConstraintDict,
    AttributeConstraintDictUtil,
    AttributeDict,
    AttributeDictUtil,
)
from translator_tom.model_dicts.auxiliary_graph import AuxiliaryGraphsDict
from translator_tom.model_dicts.constraints import (
    AgentTypeConstraintDict,
    AgentTypeConstraintDictUtil,
    KnowledgeLevelConstraintDict,
    KnowledgeLevelConstraintDictUtil,
    QEdgeConstraintsDict,
    QEdgeConstraintsDictUtil,
    SourceConstraintDict,
    SourceConstraintDictUtil,
)
from translator_tom.model_dicts.qualifier import (
    QualifierDict,
    QualifierDictUtil,
    QualifierSetConstraint,
)
from translator_tom.model_dicts.result import ResultDict, ResultDictUtil
from translator_tom.model_dicts.retrieval_source import (
    RetrievalSourceDict,
    RetrievalSourceDictUtil,
)
from translator_tom.models.knowledge_graph import Edge, KnowledgeGraph, Node
from translator_tom.models.retrieval_source import ResourceRoleEnum
from translator_tom.models.shared import CURIE, AuxGraphID, EdgeID, Infores
from translator_tom.utils.biolink import Biolink
from translator_tom.utils.dict_util_base import DictUtil
from translator_tom.utils.hash import tomhash

__all__ = [
    "EdgeDict",
    "EdgeDictUtil",
    "KnowledgeGraphDict",
    "KnowledgeGraphDictUtil",
    "NodeDict",
    "NodeDictUtil",
]


class NodeDict(TypedDict):
    name: NotRequired[str | None]
    categories: list[Biolink.Entity]
    attributes: NotRequired[list[AttributeDict] | None]
    is_set: NotRequired[bool | None]


class NodeDictUtil(DictUtil[NodeDict]):
    """Utility methods for `NodeDict`, mirroring those on the `Node` model."""

    _model = Node

    @staticmethod
    def attributes_list(node: NodeDict) -> list[AttributeDict]:
        """Get the attributes as a guaranteed list, even if they are represented as None."""
        attributes = node.get("attributes")
        return attributes if attributes is not None else []

    @classmethod
    def hash(cls, obj: NodeDict) -> str:
        """Hash matching `Node.hash` (identity by name and is_set only)."""
        # Categories/attributes are excluded: a node's identity is really its KG key.
        return tomhash((obj.get("name"), obj.get("is_set")))

    @staticmethod
    def meets_constraints(
        node: NodeDict, constraints: list[AttributeConstraintDict]
    ) -> bool:
        """Check if all constraints are satisfied by the node's attributes."""
        return AttributeConstraintDictUtil.set_met_by(
            constraints, NodeDictUtil.attributes_list(node)
        )

    @staticmethod
    def update(node: NodeDict, other: NodeDict) -> None:
        """Update the node in-place with another node.

        Does not mutate `other`.
        """
        node["name"] = other.get("name") or node.get("name")
        node["categories"] = list(set(node["categories"]) | set(other["categories"]))

        other_attrs = other.get("attributes")
        if other_attrs:
            attrs = {
                AttributeDictUtil.hash(attr): attr
                for attr in NodeDictUtil.attributes_list(node)
            }
            for attr in other_attrs:
                attrs[AttributeDictUtil.hash(attr)] = deepcopy(attr)
            node["attributes"] = list(attrs.values())


class EdgeDict(TypedDict):
    predicate: Biolink.Predicate
    subject: CURIE
    object: CURIE
    attributes: NotRequired[list[AttributeDict] | None]
    qualifiers: NotRequired[list[QualifierDict] | None]
    sources: list[RetrievalSourceDict]
    knowledge_level: str
    agent_type: str


class EdgeDictUtil(DictUtil[EdgeDict]):
    """Utility methods for `EdgeDict`, mirroring those on the `Edge` model."""

    _model = Edge

    @staticmethod
    def attributes_list(edge: EdgeDict) -> list[AttributeDict]:
        """Get the attributes as a guaranteed list, even if they are represented as None."""
        attributes = edge.get("attributes")
        return attributes if attributes is not None else []

    @staticmethod
    def qualifiers_list(edge: EdgeDict) -> list[QualifierDict]:
        """Get the qualifiers as a guaranteed list, even if they are represented as None."""
        qualifiers = edge.get("qualifiers")
        return qualifiers if qualifiers is not None else []

    @staticmethod
    def primary_knowledge_source(edge: EdgeDict) -> RetrievalSourceDict:
        """The primary knowledge source of the edge."""
        for source in edge["sources"]:
            if source["resource_role"] == ResourceRoleEnum.primary_knowledge_source:
                return source

        raise ValueError(
            f"Edge {edge['subject']} -{edge['predicate']}-> {edge['object']} has no "
            "primary_knowledge_source!"
        )

    @staticmethod
    def last_downstream_source(edge: EdgeDict) -> RetrievalSourceDict | None:
        """Get the last/most downstream source in the chain."""
        upstreams = set(
            itertools.chain(
                *[
                    source.get("upstream_resource_ids") or []
                    for source in edge["sources"]
                ]
            )
        )
        return next(
            iter(
                source
                for source in edge["sources"]
                if source["resource_id"] not in upstreams
            ),
            None,
        )

    @staticmethod
    def is_self_edge(edge: EdgeDict) -> bool:
        """Check if the edge is a self-edge."""
        return edge["subject"] == edge["object"]

    @staticmethod
    def support_graphs(edge: EdgeDict) -> list[AuxGraphID]:
        """Get the support graph IDs referenced by this edge."""
        support_graphs = list[AuxGraphID]()
        for attr in EdgeDictUtil.attributes_list(edge):
            if attr["attribute_type_id"] == Biolink("support_graphs"):
                support_graphs.extend(cast("list[AuxGraphID]", attr["value"]))
        return support_graphs

    @classmethod
    def hash(cls, obj: EdgeDict) -> str:
        """Hash matching `Edge.hash` (subject/object/predicate, qualifiers, primary KS)."""
        return tomhash(
            (
                obj["subject"],
                obj["object"],
                obj["predicate"],
                frozenset(QualifierDictUtil.hash(q) for q in cls.qualifiers_list(obj)),
                cls.primary_knowledge_source(obj)["resource_id"],
            )
        )

    @staticmethod
    def update(edge: EdgeDict, other: EdgeDict) -> None:
        """Update the edge in-place with another edge.

        Does not mutate `other`.
        """
        # New KL/AT win.
        edge["knowledge_level"] = other["knowledge_level"]
        edge["agent_type"] = other["agent_type"]

        edge_attrs = edge.get("attributes")
        other_attrs = other.get("attributes")
        if (not edge_attrs) and other_attrs:
            edge["attributes"] = [deepcopy(attr) for attr in other_attrs]
        elif edge_attrs and other_attrs:
            attrs = {AttributeDictUtil.hash(attr): attr for attr in edge_attrs}
            for attr in other_attrs:
                attrs[AttributeDictUtil.hash(attr)] = deepcopy(attr)
            edge["attributes"] = list(attrs.values())

        if (not edge["sources"]) and other["sources"]:
            edge["sources"] = [deepcopy(source) for source in other["sources"]]
        elif edge["sources"] and other["sources"]:
            sources = {
                RetrievalSourceDictUtil.hash(source): source
                for source in edge["sources"]
            }
            for other_source in other["sources"]:
                source_hash = RetrievalSourceDictUtil.hash(other_source)
                # update existing or take copy of other
                if existing := sources.get(source_hash):
                    RetrievalSourceDictUtil.update(existing, other_source)
                else:
                    sources[source_hash] = deepcopy(other_source)

            edge["sources"] = list(sources.values())

    @staticmethod
    def meets_attribute_constraints(
        edge: EdgeDict, constraints: list[AttributeConstraintDict]
    ) -> bool:
        """Check if all attribute constraints are satisfied by the edge's attributes."""
        return AttributeConstraintDictUtil.set_met_by(
            constraints, EdgeDictUtil.attributes_list(edge)
        )

    @staticmethod
    def meets_qualifier_constraints(
        edge: EdgeDict, constraints: list[QualifierSetConstraint]
    ) -> bool:
        """Check if the edge satisfies the qualifier constraints."""
        return QualifierDictUtil.constraint_set_met_by(
            constraints, EdgeDictUtil.qualifiers_list(edge)
        )

    @staticmethod
    def meets_knowledge_level_constraint(
        edge: EdgeDict, constraint: KnowledgeLevelConstraintDict
    ) -> bool:
        """Check if the edge's knowledge_level satisfies the constraint."""
        return KnowledgeLevelConstraintDictUtil.met_by(
            constraint, edge["knowledge_level"]
        )

    @staticmethod
    def meets_agent_type_constraint(
        edge: EdgeDict, constraint: AgentTypeConstraintDict
    ) -> bool:
        """Check if the edge's agent_type satisfies the constraint."""
        return AgentTypeConstraintDictUtil.met_by(constraint, edge["agent_type"])

    @staticmethod
    def meets_source_constraint(
        edge: EdgeDict, constraint: SourceConstraintDict
    ) -> bool:
        """Check if the edge's sources satisfy the constraint."""
        return SourceConstraintDictUtil.met_by(constraint, edge["sources"])

    @staticmethod
    def meets_constraints(edge: EdgeDict, constraints: QEdgeConstraintsDict) -> bool:
        """Check if the edge satisfies all of a QEdge's constraints.

        Each present constraint must be met (AND); absent constraints are ignored.
        """
        knowledge_level = constraints.get("knowledge_level")
        agent_type = constraints.get("agent_type")
        sources = constraints.get("sources")
        return (
            (
                knowledge_level is None
                or EdgeDictUtil.meets_knowledge_level_constraint(edge, knowledge_level)
            )
            and (
                agent_type is None
                or EdgeDictUtil.meets_agent_type_constraint(edge, agent_type)
            )
            and (sources is None or EdgeDictUtil.meets_source_constraint(edge, sources))
            and EdgeDictUtil.meets_attribute_constraints(
                edge, QEdgeConstraintsDictUtil.attributes_list(constraints)
            )
            and EdgeDictUtil.meets_qualifier_constraints(
                edge, QEdgeConstraintsDictUtil.qualifiers_list(constraints)
            )
        )

    @staticmethod
    def append_aggregator(edge: EdgeDict, source: Infores) -> None:
        """Append an aggregator source to the present chain with appropriate upstreams."""
        last_downstream = EdgeDictUtil.last_downstream_source(edge)
        if last_downstream is None:
            raise ValueError("Provenance chain is invalid.")
        edge["sources"].append(
            {
                "resource_id": source,
                "resource_role": "aggregator_knowledge_source",
                "upstream_resource_ids": [last_downstream["resource_id"]],
            }
        )


class KnowledgeGraphDict(TypedDict):
    nodes: dict[CURIE, NodeDict]
    edges: NotRequired[dict[EdgeID, EdgeDict] | None]


class KnowledgeGraphDictUtil(DictUtil[KnowledgeGraphDict]):
    """Utility methods for `KnowledgeGraphDict`, mirroring those on the `KnowledgeGraph` model."""

    _model = KnowledgeGraph

    @staticmethod
    def edges_dict(knowledge_graph: KnowledgeGraphDict) -> dict[EdgeID, EdgeDict]:
        """Get the edges as a guaranteed dict, even if they are represented as None."""
        edges = knowledge_graph.get("edges")
        return edges if edges is not None else {}

    @staticmethod
    def new(edges: bool = True) -> KnowledgeGraphDict:
        """Return an empty instance, without having to pass required containers."""
        knowledge_graph: KnowledgeGraphDict = {"nodes": {}}
        if edges:
            knowledge_graph["edges"] = {}
        return knowledge_graph

    @staticmethod
    def normalize(knowledge_graph: KnowledgeGraphDict) -> dict[EdgeID, EdgeID]:
        """Normalize the kgraph edge IDs and return a mapping of old:new.

        Mutates the kgraph; references to specific edges may become stale.
        """
        mapping = dict[EdgeID, EdgeID]()
        edges = knowledge_graph.get("edges")
        if edges is None:
            return mapping

        for edge_id in list(edges.keys()):
            edge = edges.pop(edge_id)
            new_id = EdgeDictUtil.hash(edge)
            mapping[edge_id] = new_id
            existing = edges.get(new_id)
            if existing is not None:
                # Copy on collision so .update()'s normalization doesn't mutate its `other`
                merged = deepcopy(existing)
                EdgeDictUtil.update(merged, edge)
                edges[new_id] = merged
            else:
                edges[new_id] = edge

        return mapping

    @staticmethod
    def update(
        knowledge_graph: KnowledgeGraphDict,
        other: KnowledgeGraphDict,
        pre_normalized: Literal["neither", "both", "self", "other"] = "neither",
        copy: bool = True,
    ) -> tuple[dict[EdgeID, EdgeID], dict[EdgeID, EdgeID]]:
        """Update the kgraph in-place using the other.

        Args:
            knowledge_graph: The kgraph to update.
            other: The other kgraph.
            pre_normalized: Which of knowledge_graph/other already have normalized
                (hash-keyed) edge IDs, to skip redundant normalization.
            copy: When True (default), `other` is copied to avoid mutation. Set to False for a mild performance improvement, when safe.

        Returns:
            `(knowledge_graph_mapping, other_mapping)` of old:new EdgeIDs, one per side
            that was normalized (empty otherwise). Kept separate because the two may
            reuse an old edge ID for different edges.
        """
        self_mapping = dict[EdgeID, EdgeID]()
        other_mapping = dict[EdgeID, EdgeID]()
        if pre_normalized in ("neither", "other"):
            self_mapping = KnowledgeGraphDictUtil.normalize(knowledge_graph)
        if pre_normalized in ("neither", "self"):
            # Normalize a shallow copy of the other dict so as not to modify the original.
            other_copy: KnowledgeGraphDict = {"nodes": dict(other["nodes"])}
            other_edges = other.get("edges")
            if other_edges is not None:
                other_copy["edges"] = dict(other_edges)
            other = other_copy
            other_mapping = KnowledgeGraphDictUtil.normalize(other)

        for node_id, node in other["nodes"].items():
            if node_id in knowledge_graph["nodes"]:
                NodeDictUtil.update(knowledge_graph["nodes"][node_id], node)
                continue
            knowledge_graph["nodes"][node_id] = deepcopy(node) if copy else node

        other_edges = other.get("edges")
        if other_edges:
            kg_edges = knowledge_graph.get("edges")
            if kg_edges is None:
                kg_edges = knowledge_graph["edges"] = {}
            for edge_id, edge in other_edges.items():
                if edge_id in kg_edges:
                    EdgeDictUtil.update(kg_edges[edge_id], edge)
                    continue
                kg_edges[edge_id] = deepcopy(edge) if copy else edge

        return self_mapping, other_mapping

    @staticmethod
    def _walk_results(
        aux_graphs: AuxiliaryGraphsDict, results: list[ResultDict]
    ) -> tuple[set[EdgeID], set[CURIE]]:
        """Walk results to find immediately bound edges and nodes."""
        bound_edges = set[EdgeID]()
        bound_nodes = set[CURIE]()
        for result in results:
            for node_binding in result["node_bindings"].values():
                bound_nodes.update(node_binding["ids"])
            for analysis in ResultDictUtil.analyses_list(result):
                for aux_id in AnalysisDictUtil.support_graphs_list(analysis):
                    bound_edges.update(aux_graphs[aux_id]["edges"])
                for edge_binding in AnalysisDictUtil.edge_bindings_dict(
                    analysis
                ).values():
                    bound_edges.update(edge_binding["ids"])
                for path_binding in AnalysisDictUtil.path_bindings_dict(
                    analysis
                ).values():
                    for aux_id in path_binding["ids"]:
                        bound_edges.update(aux_graphs[aux_id]["edges"])
        return bound_edges, bound_nodes

    @staticmethod
    def prune(
        knowledge_graph: KnowledgeGraphDict,
        aux_graphs: AuxiliaryGraphsDict,
        results: list[ResultDict],
    ) -> None:
        """Remove any unused nodes or edges.

        Args:
          knowledge_graph: The kgraph to prune.
          aux_graphs: Auxiliary graphs using this KG.
          results: Results list using this KG.

        Raises:
          KeyError: If nodes/edges are referenced that aren't present in the KG.
        """
        bound_edges, bound_nodes = KnowledgeGraphDictUtil._walk_results(
            aux_graphs, results
        )
        edges = KnowledgeGraphDictUtil.edges_dict(knowledge_graph)

        checked_edges = set[EdgeID]()
        edges_to_check = list(bound_edges)
        while len(edges_to_check) > 0:
            edge_id = edges_to_check.pop()

            # Avoid infinite loops if edge and aux graph reference each other
            if edge_id in checked_edges:
                continue
            checked_edges.add(edge_id)

            edge = edges[edge_id]

            bound_edges.add(edge_id)
            bound_nodes.add(edge["subject"])
            bound_nodes.add(edge["object"])

            edge_aux_graphs = next(
                (
                    attr
                    for attr in EdgeDictUtil.attributes_list(edge)
                    if attr["attribute_type_id"] == "biolink:support_graphs"
                ),
                None,
            )
            if edge_aux_graphs is None:
                continue
            # Support graphs always have a value of type list[str], but the attribute
            # value is generally typed Any.
            for aux_graph_id in cast("list[str]", edge_aux_graphs["value"]):
                edges_to_check.extend(aux_graphs[aux_graph_id]["edges"])

        knowledge_graph["edges"] = {
            edge_id: edges[edge_id] for edge_id in bound_edges
        } or None
        knowledge_graph["nodes"] = {
            curie: knowledge_graph["nodes"][curie] for curie in bound_nodes
        }
