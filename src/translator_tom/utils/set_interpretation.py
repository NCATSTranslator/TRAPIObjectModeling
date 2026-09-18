"""Version- and layer-agnostic core of the set-interpretation solver.

Every `solve_set_interpretation` site (v2_0/v1_6, model/dict) shares this core.
Each site stamps its concrete objects into plain strings -- QNode ids, knode
CURIEs, qedge ids -- runs `solve`, then materializes the results back. Solving in
strings lets one implementation own the grouping, edge-aware adjacency checks, and
COLLATE maximal-clique logic regardless of representation.
"""

from __future__ import annotations

import itertools
from collections import defaultdict
from collections.abc import Container
from dataclasses import dataclass
from typing import NamedTuple

from translator_tom.utils.shared import CURIE, QEdgeID, QNodeID

__all__ = ["QNodeSpec", "QueryStamp", "ResultStamp", "SolvedResult", "solve"]

# Default cap on maximal cliques per COLLATE cluster (count can blow up ~3^(n/3)).
_MAX_COLLATE_CLIQUES = 4096

# One Result stamped to `{qnode: knode}` -- one knode per QNode.
ResultStamp = dict[QNodeID, CURIE]

# A ResultStamp paired with its index into the input results.
_IndexedResultStamp = tuple[int, ResultStamp]

# A simplified ALL QNode
_AllNodeStamp = tuple[CURIE, set[CURIE]]

# Every ALL QNode mapped to its (member_id, members).
_AllSets = dict[QNodeID, _AllNodeStamp]

# Each QNode's incident (qedge_id, other_qnode) pairs.
_IncidentEdges = dict[QNodeID, list[tuple[QEdgeID, QNodeID]]]

# A compatibility-graph vertex: one (qnode, candidate knode) pairing.
_Vertex = tuple[QNodeID, CURIE]

# Per-qedge adjacency: within a result group, each vertex mapped to the vertices it co-binds with.
_Adjacency = dict[QEdgeID, dict[_Vertex, set[_Vertex]]]

# A batch-group key: the (qnode, knode) BATCH bindings a group of results shares.
_BatchKey = frozenset[tuple[QNodeID, CURIE]]


class QNodeSpec(NamedTuple):
    """A QNode's set-interpretation inputs, stamped from the query graph."""

    mode: str
    ids: list[CURIE]
    member_ids: list[CURIE]


class QueryStamp(NamedTuple):
    """The query graph stamped into plain strings for `solve`."""

    qnodes: dict[QNodeID, QNodeSpec]
    qedges: dict[QEdgeID, tuple[QNodeID, QNodeID]]


class SolvedResult(NamedTuple):
    """One solved result: set-node bindings to overwrite, plus backing results.

    `set_bindings` covers only ALL/COLLATE nodes (batch bindings are kept from the
    base result); `backing_indices` is indices into the input `result_stamps`.
    """

    set_bindings: dict[QNodeID, list[CURIE]]
    backing_indices: list[int]


def solve(  # noqa: PLR0913
    query: QueryStamp,
    result_stamps: list[ResultStamp],
    knode_ids: Container[CURIE],
    *,
    skip_many: bool = False,
    max_collate_candidates: int = 64,
    max_collate_cliques: int = _MAX_COLLATE_CLIQUES,
) -> list[SolvedResult]:
    """Solve set interpretation over a stamped query and result stamps.

    BATCH keys the grouping.
    ALL binds its set node; every member must be edge-connected to its neighbors,
    else the batch-group is dropped.
    COLLATE binds every node edge-connected to its neighbors; adjacent COLLATE
    nodes split into maximal complete-multipartite groups (multiple results).

    Args:
        query: The stamped query graph (qnodes + qedges).
        result_stamps: One `ResultStamp` per input Result.
        knode_ids: Knowledge-graph node ids (for the ALL member-presence check).
        skip_many: Treat MANY nodes as BATCH instead of raising.
        max_collate_candidates: Reject a connected COLLATE cluster with more
            candidates than this (0 rejects any adjacent COLLATE, a negative value
            disables the cap); enumeration also raises past `max_collate_cliques`.
        max_collate_cliques: Raise if a COLLATE cluster enumerates more maximal
            cliques than this (a negative value disables the cap); guards dense
            clusters whose clique count can blow up ~3^(n/3).

    Returns:
        One `SolvedResult` per maximal grouping; `backing_indices` indexes into `result_stamps`.
    """
    all_nodes, collate_nodes = _resolve_modes(query.qnodes, skip_many)
    set_nodes = set(all_nodes) | collate_nodes
    incident = _get_incident_edges(query.qedges)
    collate_clusters = _get_collate_clusters(collate_nodes, incident)  # query-invariant
    set_edges = {qe for sn in set_nodes for qe, _ in incident.get(sn, [])}
    _check_all_node_members_present(all_nodes, knode_ids)

    batch_groups = defaultdict[_BatchKey, list[_IndexedResultStamp]](list)
    for result_index, result_stamp in enumerate(result_stamps):
        batch_key = frozenset(
            (qnode_id, knode_id)
            for qnode_id, knode_id in result_stamp.items()
            if qnode_id not in set_nodes
        )
        batch_groups[batch_key].append((result_index, result_stamp))

    solved = list[SolvedResult]()
    for batch_group in batch_groups.values():
        solved.extend(
            _solve_group(
                batch_group,
                all_nodes,
                collate_nodes,
                collate_clusters,
                incident,
                set_edges,
                max_collate_candidates,
                max_collate_cliques,
            )
        )
    return solved


def _resolve_modes(
    qnodes: dict[QNodeID, QNodeSpec], skip_many: bool
) -> tuple[_AllSets, set[QNodeID]]:
    """Map each ALL node to `(member_id, members)` and collect COLLATE nodes.

    MANY raises unless `skip_many`. An ALL node with no `ids` or no members falls
    back to BATCH by omission.

    Args:
        qnodes: Each QNode's `QNodeSpec`.
        skip_many: Treat MANY nodes as BATCH instead of raising.

    Returns:
        `(all_sets, collate_nodes)`: ALL nodes mapped to `(member_id, members)`, and
        the set of COLLATE node ids.
    """
    modes = {qnode_id: (spec.mode or "BATCH") for qnode_id, spec in qnodes.items()}
    many = [qnode_id for qnode_id, mode in modes.items() if mode == "MANY"]
    if many and not skip_many:
        raise ValueError(
            f"set_interpretation MANY is not supported (nodes {sorted(many)}); "
            "pass skip_many=True to treat them as BATCH."
        )

    collate = {qnode_id for qnode_id, mode in modes.items() if mode == "COLLATE"}

    # Build ALL node sets
    all_nodes = _AllSets()
    for qnode_id, mode in modes.items():
        if mode != "ALL":
            continue
        spec = qnodes[qnode_id]
        members = spec.member_ids or spec.ids
        if spec.ids and members:
            all_nodes[qnode_id] = (spec.ids[0], set(members))
    return all_nodes, collate


def _get_incident_edges(
    qedges: dict[QEdgeID, tuple[QNodeID, QNodeID]],
) -> _IncidentEdges:
    """Map each QNode to its incident `(qedge_id, other_qnode)` pairs.

    Args:
        qedges: qedge id -> `(subject, object)` QNode ids.

    Returns:
        QNode id -> list of its `(qedge_id, other_qnode)` incident pairs.
    """
    incident = defaultdict[QNodeID, list[tuple[QEdgeID, QNodeID]]](list)
    for qedge_id, (subject, obj) in qedges.items():
        incident[subject].append((qedge_id, obj))
        incident[obj].append((qedge_id, subject))
    return incident


def _check_all_node_members_present(
    all_sets: _AllSets, knode_ids: Container[CURIE]
) -> None:
    """Raise if any ALL member node is missing from the knowledge graph.

    Args:
        all_sets: ALL nodes mapped to `(member_id, members)`.
        knode_ids: Knowledge-graph node ids.
    """
    for qnode_id, (member_id, _) in all_sets.items():
        if member_id not in knode_ids:
            raise ValueError(
                f"ALL node '{qnode_id}' binds member node '{member_id}', which is absent "
                "from the knowledge_graph."
            )


def _solve_group(  # noqa: PLR0913
    group: list[_IndexedResultStamp],
    all_nodes: _AllSets,
    collate_nodes: set[QNodeID],
    collate_clusters: list[list[QNodeID]],
    incident: _IncidentEdges,
    set_edges: set[QEdgeID],
    max_collate_candidates: int,
    max_collate_cliques: int,
) -> list[SolvedResult]:
    """Solve one batch-group (0+ results, one per maximal COLLATE grouping).

    Args:
        group: The group's tagged `ResultStamp`s (index + stamp), sharing BATCH bindings.
        all_nodes: ALL nodes mapped to `(member_id, members)`.
        collate_nodes: The COLLATE node ids.
        collate_clusters: Connected COLLATE clusters (query-invariant, precomputed).
        incident: QNode id -> `(qedge_id, other_qnode)` incident pairs.
        set_edges: qedges incident to a set node (the only adjacency ever read).
        max_collate_candidates: Cap on a COLLATE cluster's candidate count.
        max_collate_cliques: Cap on maximal cliques enumerated per COLLATE cluster.

    Returns:
        One `SolvedResult` per maximal COLLATE grouping; empty if unsatisfiable.
    """
    group_stamps = [stamp for _, stamp in group]
    adjacency = _build_adjacency(group_stamps, incident, set_edges)
    first = group_stamps[0]  # Can use first because all BATCH nodes match
    batch_binding = {
        qnode_id: knode_id
        for qnode_id, knode_id in first.items()
        if qnode_id not in all_nodes and qnode_id not in collate_nodes
    }

    # Check ALL nodes are satisfied
    for qnode_id, (_, members) in all_nodes.items():
        if not _all_satisfied(
            qnode_id,
            members,
            incident.get(qnode_id, []),
            adjacency,
            batch_binding,
            all_nodes,
        ):
            return []

    # Collect and edge-filter each COLLATE node's candidate knodes
    filtered_candidates = dict[QNodeID, list[CURIE]]()
    for qnode_id in collate_nodes:
        candidates = list(
            dict.fromkeys(
                result_stamp[qnode_id]
                for result_stamp in group_stamps
                if qnode_id in result_stamp
            )
        )
        filtered_candidates[qnode_id] = _get_collate_candidates(
            qnode_id,
            candidates,
            incident.get(qnode_id, []),
            adjacency,
            batch_binding,
            all_nodes,
        )

    # Enumerate each connected COLLATE cluster's collation options (bail if none)
    collation_options_by_cluster = list[list[dict[QNodeID, list[CURIE]]]]()
    for cluster in collate_clusters:
        # Length-1 cluster is a COLLATE node connected only to ALL/BATCH node(s)
        collation_options = _get_collation_options(
            cluster,
            filtered_candidates,
            adjacency,
            incident,
            max_collate_candidates,
            max_collate_cliques,
        )
        if not collation_options:
            return []
        collation_options_by_cluster.append(collation_options)

    # Build one result per collation-option combination across clusters, dropping unbacked
    results = list[SolvedResult]()
    for combo in itertools.product(*collation_options_by_cluster):
        assignment = dict[QNodeID, list[CURIE]]()
        for collation_option in combo:
            assignment.update(collation_option)
        built = _build_solved(group, all_nodes, assignment)
        if built is not None:
            results.append(built)
    return results


def _build_adjacency(
    group_stamps: list[ResultStamp],
    incident: _IncidentEdges,
    set_edges: set[QEdgeID],
) -> _Adjacency:
    """Per-qedge adjacency `{qedge: {vertex: co-bound vertices}}`, from the group's stamps.

    Only `set_edges` are built -- adjacency is read solely for set-node-incident qedges.

    Args:
        group_stamps: The group's `ResultStamp`s.
        incident: QNode id -> `(qedge_id, other_qnode)` incident pairs.
        set_edges: qedges incident to a set node (others are skipped, never read).

    Returns:
        qedge_id -> `{(qnode, knode): set of co-bound (qnode, knode) vertices}`.
    """
    if not set_edges:
        return {}
    adjacency = defaultdict[QEdgeID, dict[_Vertex, set[_Vertex]]](dict)
    for stamp in group_stamps:
        for qnode_id, edges in incident.items():
            subject = stamp.get(qnode_id)
            if subject is None:
                continue
            # Keyed by qnode, so a self-edge (subject == obj) is two distinct vertices
            vertex = (qnode_id, subject)
            for qedge_id, other in edges:
                if qedge_id not in set_edges:
                    continue
                obj = stamp.get(other)
                if obj is not None:
                    adjacency[qedge_id].setdefault(vertex, set()).add((other, obj))
    return adjacency


def _all_satisfied(  # noqa: PLR0913
    qnode_id: QNodeID,
    members: set[CURIE],
    edges: list[tuple[QEdgeID, QNodeID]],
    adjacency: _Adjacency,
    batch_binding: dict[QNodeID, CURIE],
    all_sets: _AllSets,
) -> bool:
    """Whether every member is edge-connected per each incident BATCH/ALL edge.

    Args:
        qnode_id: The ALL node these members belong to.
        members: The ALL node's required member knodes.
        edges: The ALL node's `(qedge_id, other_qnode)` incident pairs.
        adjacency: Per-qedge `{vertex: co-bound vertices}` map.
        batch_binding: BATCH node id -> its bound knode.
        all_sets: ALL nodes mapped to `(member_id, members)`.

    Returns:
        True if every member satisfies each BATCH/ALL adjacency, else False.
    """
    for qedge_id, other in edges:
        edge_adj = adjacency.get(qedge_id, {})
        if other in batch_binding:
            # ALL-BATCH: every member must edge-connect to the neighbor's single bound knode.
            target = (other, batch_binding[other])
            if not all(target in edge_adj.get((qnode_id, m), ()) for m in members):
                return False
        elif other in all_sets:
            # ALL-ALL (directional; caller checks the reciprocal): every member edge-connected to >=1 other-set member.
            others = all_sets[other][1]
            if not all(
                any((other, m2) in edge_adj.get((qnode_id, m), ()) for m2 in others)
                for m in members
            ):
                return False
    return True


def _get_collate_candidates(  # noqa: PLR0913
    qnode_id: QNodeID,
    candidates: list[CURIE],
    edges: list[tuple[QEdgeID, QNodeID]],
    adjacency: _Adjacency,
    batch_binding: dict[QNodeID, CURIE],
    all_sets: _AllSets,
) -> list[CURIE]:
    """Order-stable collated knodes kept by every incident BATCH/ALL edge.

    Args:
        qnode_id: The COLLATE node these candidates belong to.
        candidates: The COLLATE node's candidate knodes, in order.
        edges: The COLLATE node's `(qedge_id, other_qnode)` incident pairs.
        adjacency: Per-qedge `{vertex: co-bound vertices}` map.
        batch_binding: BATCH node id -> its bound knode.
        all_sets: ALL nodes mapped to `(member_id, members)`.

    Returns:
        The candidates edge-connected to every BATCH/ALL neighbor.
    """
    for qedge_id, other in edges:
        edge_adj = adjacency.get(qedge_id, {})
        if other in batch_binding:
            # COLLATE-BATCH: keep candidates that edge-connect to the neighbor's single bound knode.
            target = (other, batch_binding[other])
            candidates = [
                c for c in candidates if target in edge_adj.get((qnode_id, c), ())
            ]
        elif other in all_sets:
            # COLLATE-ALL: keep candidates that edge-connect to every member of the other set.
            members = all_sets[other][1]
            candidates = [
                c
                for c in candidates
                if all((other, m) in edge_adj.get((qnode_id, c), ()) for m in members)
            ]
    return candidates


def _get_collate_clusters(
    collate_nodes: set[QNodeID],
    incident: _IncidentEdges,
) -> list[list[QNodeID]]:
    """Connected clusters of COLLATE nodes linked by COLLATE-COLLATE qedges.

    Args:
        collate_nodes: The COLLATE node ids.
        incident: QNode id -> `(qedge_id, other_qnode)` incident pairs.

    Returns:
        Sorted node lists, one per connected cluster.
    """
    # Build COLLATE-COLLATE adjacency (edges to BATCH/ALL neighbors are ignored)
    neighbors = defaultdict[QNodeID, set[QNodeID]](set)
    for qnode_id in collate_nodes:
        for _, other in incident.get(qnode_id, []):
            if other in collate_nodes:
                neighbors[qnode_id].add(other)

    # Flood-fill each unseen COLLATE node into its connected cluster
    seen = set[QNodeID]()
    clusters = list[list[QNodeID]]()
    for start_node in sorted(collate_nodes):
        if start_node in seen:
            continue
        stack, cluster = [start_node], list[QNodeID]()
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            cluster.append(node)
            stack.extend(neighbors[node] - seen)
        clusters.append(sorted(cluster))
    return clusters


def _get_collation_options(  # noqa: PLR0913
    cluster: list[QNodeID],
    filtered_candidates: dict[QNodeID, list[CURIE]],
    adj: _Adjacency,
    incident: _IncidentEdges,
    max_collate_candidates: int,
    max_collate_cliques: int,
) -> list[dict[QNodeID, list[CURIE]]]:
    """Maximal complete-multipartite bindings covering every node in the cluster.

    Args:
        cluster: The COLLATE node ids in one connected cluster.
        filtered_candidates: Each COLLATE node's candidates surviving its BATCH/ALL edge filters.
        adj: Per-qedge connected `(qnode, knode)` vertex pairs.
        incident: QNode id -> `(qedge_id, other_qnode)` incident pairs.
        max_collate_candidates: Cap on the cluster's total candidate count;
            0 rejects any adjacent COLLATE, a negative value disables the cap.
        max_collate_cliques: Cap on maximal cliques enumerated for the cluster.

    Returns:
        One `{qnode: knodes}` collation option per maximal covering grouping.
    """
    # Lone COLLATE node: all surviving candidates collate into a single option
    if len(cluster) == 1:
        qnode_id = cluster[0]
        return (
            [{qnode_id: filtered_candidates[qnode_id]}]
            if filtered_candidates[qnode_id]
            else []
        )

    # Fail if cluster is oversized
    total = sum(len(filtered_candidates[qnode_id]) for qnode_id in cluster)
    if max_collate_candidates >= 0 and total > max_collate_candidates:
        raise ValueError(
            f"COLLATE cluster {cluster} has {total} candidates, exceeding "
            f"max_collate_candidates={max_collate_candidates}."
        )

    # Build the compatibility graph over every node's candidate (qnode, knode) vertices
    vertices = [
        (qnode_id, candidate_knode_id)
        for qnode_id in cluster
        for candidate_knode_id in filtered_candidates[qnode_id]
    ]
    neighbors = _get_compatibility(vertices, cluster, adj, incident)

    # Each maximal clique covering every cluster node becomes one collation option
    cluster_set = set(cluster)
    collation_options: list[dict[QNodeID, list[CURIE]]] = []
    for clique in _maximal_cliques(
        vertices, neighbors, max_collate_cliques, cluster_set
    ):
        chosen = defaultdict[QNodeID, set[CURIE]](set)
        for qnode_id, candidate_knode_id in clique:
            chosen[qnode_id].add(candidate_knode_id)
        if set(chosen) != cluster_set:
            continue
        collation_options.append(
            {
                qnode_id: [
                    curie
                    for curie in filtered_candidates[qnode_id]
                    if curie in chosen[qnode_id]
                ]
                for qnode_id in cluster
            }
        )
    collation_options.sort(
        key=lambda opt: tuple((qnode_id, tuple(opt[qnode_id])) for qnode_id in cluster)
    )
    return collation_options


def _cluster_qedges(
    cluster: list[QNodeID], incident: _IncidentEdges
) -> dict[frozenset[QNodeID], list[QEdgeID]]:
    """Map each COLLATE-COLLATE node pair in the cluster to the qedges joining them.

    Args:
        cluster: The COLLATE node ids in one connected cluster.
        incident: QNode id -> `(qedge_id, other_qnode)` incident pairs.

    Returns:
        `frozenset({qnodeA, qnodeB})` -> the qedges joining that in-cluster pair.
    """
    cluster_set = set(cluster)
    qedges_between = defaultdict[frozenset[QNodeID], list[QEdgeID]](list)
    for qnode_id in cluster:
        for qedge_id, other in incident.get(qnode_id, []):
            key = frozenset((qnode_id, other))
            if (
                other in cluster_set  # other is part of the cluster
                and other != qnode_id  # ...and not self
                and qedge_id not in qedges_between[key]  # ...and not already found
            ):
                qedges_between[key].append(qedge_id)
    return qedges_between


def _get_compatibility(
    vertices: list[_Vertex],
    cluster: list[QNodeID],
    adj: _Adjacency,
    incident: _IncidentEdges,
) -> dict[_Vertex, set[_Vertex]]:
    """Compatibility graph: same qnode / non-adjacent qnodes / edge-connected pairs.

    Args:
        vertices: `(qnode, knode)` candidates in the cluster.
        cluster: The COLLATE node ids in the cluster.
        adj: Per-qedge `{vertex: co-bound vertices}` map.
        incident: QNode id -> `(qedge_id, other_qnode)` incident pairs.

    Returns:
        Each vertex mapped to its set of compatible vertices.
    """
    qedges_between = _cluster_qedges(cluster, incident)

    # Group vertices by qnode; build the graph a qnode-block at a time (not all-pairs)
    by_qnode = defaultdict[QNodeID, list[_Vertex]](list)
    for vertex in vertices:
        by_qnode[vertex[0]].append(vertex)
    cluster_qnodes = list(by_qnode)

    neighbors = {v: set[_Vertex]() for v in vertices}
    for i, qnode_u in enumerate(cluster_qnodes):
        block_u = set(by_qnode[qnode_u])
        # Same qnode: every pair is compatible (a clique)
        for u in block_u:
            neighbors[u] |= block_u
            neighbors[u].discard(u)
        for qnode_v in cluster_qnodes[i + 1 :]:
            block_v = set(by_qnode[qnode_v])
            qedge_ids = qedges_between.get(frozenset((qnode_u, qnode_v)))
            if not qedge_ids:
                # Non-adjacent qnodes: complete bipartite between the blocks
                for u in block_u:
                    neighbors[u] |= block_v
                for w in block_v:
                    neighbors[w] |= block_u
            else:
                # Adjacent qnodes: read edge-connected partners from adjacency (sparse)
                for u in block_u:
                    for w in _edge_connected(u, qedge_ids, adj) & block_v:
                        neighbors[u].add(w)
                        neighbors[w].add(u)
    return neighbors


def _edge_connected(
    vertex: _Vertex, qedge_ids: list[QEdgeID], adj: _Adjacency
) -> set[_Vertex]:
    """Vertices co-bound with `vertex` on every one of `qedge_ids`.

    Args:
        vertex: The `(qnode, knode)` to find partners for.
        qedge_ids: The qedges that must all connect vertex to a partner.
        adj: Per-qedge `{vertex: co-bound vertices}` map.

    Returns:
        The intersection of co-bound vertices across every qedge (empty if any is).
    """
    partners: set[_Vertex] | None = None
    for qedge_id in qedge_ids:
        nb = adj.get(qedge_id, {}).get(vertex, set())
        partners = nb if partners is None else partners & nb
        if not partners:
            return set()
    return partners or set()


@dataclass
class _CliqueFrame:
    """One node of the iterative Bron-Kerbosch search (R=`clique`, P=`candidates`, X=`excluded`)."""

    clique: frozenset[_Vertex]
    candidates: set[_Vertex]
    excluded: set[_Vertex]
    branch: list[_Vertex]  # candidates still to try (popped one per visit)
    last: _Vertex | None = None  # the vertex branched on last visit, to retire (P -> X)


def _maximal_cliques(
    vertices: list[_Vertex],
    neighbors: dict[_Vertex, set[_Vertex]],
    max_collate_cliques: int,
    required_qnodes: set[QNodeID],
) -> list[frozenset[_Vertex]]:
    """Enumerate maximal cliques via iterative Bron-Kerbosch with pivoting.

    Iterative (an explicit frame stack) so a deep clique -- e.g. one qnode's whole
    candidate set, which is itself a clique -- can't blow Python's recursion limit.
    Branches that can no longer cover every `required_qnodes` are pruned (the caller
    keeps only full-coverage cliques), which cuts the large single-qnode cliques.

    Args:
        vertices: All vertices of the compatibility graph.
        neighbors: Each vertex mapped to its compatible vertices.
        max_collate_cliques: Raise past this many cliques (negative disables).
        required_qnodes: Every emitted clique must span these qnodes (`v[0]`).

    Returns:
        The maximal cliques (each spanning `required_qnodes`), as frozensets of vertices.

    Raises:
        ValueError: If enumeration exceeds `max_collate_cliques`.
    """
    cliques = list[frozenset[_Vertex]]()

    def make_frame(
        clique: frozenset[_Vertex], candidates: set[_Vertex], excluded: set[_Vertex]
    ) -> _CliqueFrame | None:
        """Record `clique` if it is maximal, else return a frame to branch from."""
        # Prune branches that can never span every required qnode (caller drops them)
        covered = {v[0] for v in clique}
        covered.update(v[0] for v in candidates)
        if not required_qnodes <= covered:
            return None
        # Maximal clique reached: nothing left to add and nothing already excluded
        if not candidates and not excluded:
            cliques.append(clique)
            if 0 <= max_collate_cliques < len(cliques):
                raise ValueError(
                    f"COLLATE grouping exceeded {max_collate_cliques} maximal cliques; "
                    "the cluster is too densely interconnected to enumerate."
                )
            return None
        # Pivot on the highest-degree vertex; branch only on candidates it doesn't cover
        pivot = max(candidates | excluded, key=lambda u: len(candidates & neighbors[u]))
        return _CliqueFrame(
            clique, candidates, excluded, list(candidates - neighbors[pivot])
        )

    stack = list[_CliqueFrame]()
    if (seed := make_frame(frozenset(), set(vertices), set())) is not None:
        stack.append(seed)
    while stack:
        frame = stack[-1]
        # Retire the vertex branched on last visit before advancing (P -> X)
        if frame.last is not None:
            frame.candidates.discard(frame.last)
            frame.excluded.add(frame.last)
            frame.last = None
        if not frame.branch:
            stack.pop()
            continue

        v = frame.branch.pop()
        frame.last = v
        child = make_frame(
            frame.clique | {v},
            frame.candidates & neighbors[v],
            frame.excluded & neighbors[v],
        )
        if child is not None:
            stack.append(child)
    return cliques


def _stamp_matches_assignment(
    result_stamp: ResultStamp,
    all_sets: _AllSets,
    collate_sets: dict[QNodeID, set[CURIE]],
) -> bool:
    """Whether a result's bindings fall within this assignment's ALL members and COLLATE picks.

    Args:
        result_stamp: One result's `{qnode: knode}` bindings.
        all_sets: ALL nodes mapped to `(member_id, members)`.
        collate_sets: Each COLLATE node's chosen knodes as a set.

    Returns:
        True if every bound ALL/COLLATE node lands in its allowed knodes.
    """
    in_all_members = all(
        result_stamp[qnode_id] in members
        for qnode_id, (_, members) in all_sets.items()
        if qnode_id in result_stamp
    )
    in_collate_picks = all(
        result_stamp[qnode_id] in kept
        for qnode_id, kept in collate_sets.items()
        if qnode_id in result_stamp
    )
    return in_all_members and in_collate_picks


def _build_solved(
    group: list[_IndexedResultStamp],
    all_sets: _AllSets,
    collate_binding: dict[QNodeID, list[CURIE]],
) -> SolvedResult | None:
    """Assemble a `SolvedResult` for a chosen assignment, or None if unbacked.

    Args:
        group: The group's tagged `ResultStamp`s (index + stamp).
        all_sets: ALL nodes mapped to `(member_id, members)`.
        collate_binding: Each COLLATE node's chosen knodes.

    Returns:
        The set-node bindings + backing result indices, or None if no result backs
        the assignment (e.g. a spurious cross-cluster combination).
    """
    # Keep input results consistent with this assignment (ALL members + COLLATE picks)
    collate_sets = {qnode_id: set(ids) for qnode_id, ids in collate_binding.items()}
    backing_indices = [
        index
        for index, stamp in group
        if _stamp_matches_assignment(stamp, all_sets, collate_sets)
    ]
    if not backing_indices:
        return None

    # Bind ALL nodes to their member id and COLLATE nodes to their chosen knodes
    set_bindings = {
        qnode_id: [member_id] for qnode_id, (member_id, _) in all_sets.items()
    }
    set_bindings.update(collate_binding)
    return SolvedResult(set_bindings, backing_indices)
