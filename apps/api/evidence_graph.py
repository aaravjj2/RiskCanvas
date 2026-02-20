"""
evidence_graph.py (v5.54.0 — Wave 65)

Evidence Graph v1 — builds a deterministic graph connecting all RiskCanvas
entities and their relationships.

Nodes: dataset, scenario, run, job, artifact, attestation, review,
       compliance_pack, decision_packet
Edges: created_from, uses, produces, attests, approves, exports,
       belongs_to_tenant

Endpoints:
  GET /evidence/graph?tenant_id=&root_type=&root_id=&depth=
  GET /evidence/graph/summary?tenant_id=
"""
from __future__ import annotations

import hashlib
import json
import os
from collections import defaultdict
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

ASOF = "2026-02-19T00:00:00Z"
DEMO_MODE = os.getenv("DEMO_MODE", "1") == "1"

router = APIRouter(prefix="/evidence", tags=["evidence"])

# ── Node type constants ────────────────────────────────────────────────────────

NODE_TYPES = [
    "dataset", "scenario", "run", "job", "artifact",
    "attestation", "review", "compliance_pack", "decision_packet",
]

EDGE_TYPES = [
    "created_from", "uses", "produces", "attests", "approves",
    "exports", "belongs_to_tenant",
]

# ── Fixed DEMO graph fixtures ──────────────────────────────────────────────────

_DEMO_NODES: List[Dict[str, Any]] = [
    {"node_id": "ds-prov-001", "node_type": "dataset",  "label": "Demo Rates Dataset",   "tenant_id": "demo-tenant"},
    {"node_id": "ds-prov-002", "node_type": "dataset",  "label": "Demo Credit Curves",    "tenant_id": "demo-tenant"},
    {"node_id": "scen-001",    "node_type": "scenario", "label": "Rate Shock +100bps",     "tenant_id": "demo-tenant"},
    {"node_id": "scen-002",    "node_type": "scenario", "label": "Credit Event EUR",       "tenant_id": "demo-tenant"},
    {"node_id": "run-001",     "node_type": "run",      "label": "Run scen-001 2026-02-19","tenant_id": "demo-tenant"},
    {"node_id": "run-002",     "node_type": "run",      "label": "Run scen-002 2026-02-19","tenant_id": "demo-tenant"},
    {"node_id": "job-001",     "node_type": "job",      "label": "Job run-001 pricing",    "tenant_id": "demo-tenant"},
    {"node_id": "art-001",     "node_type": "artifact", "label": "Risk Report run-001",    "tenant_id": "demo-tenant"},
    {"node_id": "attest-001",  "node_type": "attestation","label": "Attestation run-001", "tenant_id": "demo-tenant"},
    {"node_id": "review-001",  "node_type": "review",   "label": "Review run-001",         "tenant_id": "demo-tenant"},
    {"node_id": "comp-001",    "node_type": "compliance_pack","label": "Compliance Pack Feb 2026","tenant_id": "demo-tenant"},
    {"node_id": "dp-001",      "node_type": "decision_packet","label": "Decision Packet Feb 2026","tenant_id": "demo-tenant"},
]

_DEMO_EDGES: List[Dict[str, Any]] = [
    {"edge_id": "e-001", "src": "scen-001", "dst": "ds-prov-001", "edge_type": "uses"},
    {"edge_id": "e-002", "src": "scen-002", "dst": "ds-prov-002", "edge_type": "uses"},
    {"edge_id": "e-003", "src": "run-001",  "dst": "scen-001",    "edge_type": "created_from"},
    {"edge_id": "e-004", "src": "run-002",  "dst": "scen-002",    "edge_type": "created_from"},
    {"edge_id": "e-005", "src": "job-001",  "dst": "run-001",     "edge_type": "created_from"},
    {"edge_id": "e-006", "src": "art-001",  "dst": "run-001",     "edge_type": "produces"},
    {"edge_id": "e-007", "src": "attest-001","dst": "run-001",    "edge_type": "attests"},
    {"edge_id": "e-008", "src": "review-001","dst": "run-001",    "edge_type": "approves"},
    {"edge_id": "e-009", "src": "comp-001", "dst": "attest-001",  "edge_type": "exports"},
    {"edge_id": "e-010", "src": "dp-001",   "dst": "comp-001",    "edge_type": "exports"},
    {"edge_id": "e-011", "src": "dp-001",   "dst": "review-001",  "edge_type": "exports"},
]

# Runtime mutable store (seed with demo data)
_GRAPH_NODES: Dict[str, Dict[str, Any]] = {n["node_id"]: n for n in _DEMO_NODES}
_GRAPH_EDGES: Dict[str, Dict[str, Any]] = {e["edge_id"]: e for e in _DEMO_EDGES}


# ── Helpers ────────────────────────────────────────────────────────────────────


def _stable_hash(data: Any) -> str:
    raw = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _bfs(start_id: str, depth: int, edges: List[Dict]) -> List[str]:
    """BFS from start_id collecting reachable node_ids up to depth."""
    visited: set = {start_id}
    frontier = [start_id]
    for _ in range(depth):
        next_frontier = []
        for nid in frontier:
            for e in edges:
                if e["src"] == nid and e["dst"] not in visited:
                    visited.add(e["dst"])
                    next_frontier.append(e["dst"])
                elif e["dst"] == nid and e["src"] not in visited:
                    visited.add(e["src"])
                    next_frontier.append(e["src"])
        frontier = next_frontier
        if not frontier:
            break
    return sorted(visited)  # stable sort


# ── Endpoints ──────────────────────────────────────────────────────────────────


class AddNodeRequest(BaseModel):
    node_id: str
    node_type: str
    label: str
    tenant_id: str = "demo-tenant"
    metadata: Optional[Dict[str, Any]] = None


class AddEdgeRequest(BaseModel):
    src: str
    dst: str
    edge_type: str
    tenant_id: str = "demo-tenant"
    metadata: Optional[Dict[str, Any]] = None


@router.get("/graph")
def get_graph(
    tenant_id: str = Query("demo-tenant"),
    root_type: Optional[str] = Query(None),
    root_id: Optional[str] = Query(None),
    depth: int = Query(3, ge=1, le=10),
):
    """Return the evidence graph for a tenant, optionally rooted at a node."""
    all_nodes = [n for n in _GRAPH_NODES.values() if n["tenant_id"] == tenant_id]
    all_edges = [e for e in _GRAPH_EDGES.values()]

    if root_id:
        visible_ids = set(_bfs(root_id, depth, all_edges))
        nodes = [n for n in all_nodes if n["node_id"] in visible_ids]
        edges = [e for e in all_edges if e["src"] in visible_ids and e["dst"] in visible_ids]
    else:
        nodes = all_nodes
        edges = all_edges

    # Stable ordering
    nodes_sorted = sorted(nodes, key=lambda n: (n["node_type"], n["node_id"]))
    edges_sorted = sorted(edges, key=lambda e: (e["edge_type"], e["src"], e["dst"]))

    graph_hash = _stable_hash({"nodes": nodes_sorted, "edges": edges_sorted})

    return {
        "tenant_id": tenant_id,
        "root_id": root_id,
        "root_type": root_type,
        "depth": depth,
        "nodes": nodes_sorted,
        "edges": edges_sorted,
        "node_count": len(nodes_sorted),
        "edge_count": len(edges_sorted),
        "graph_hash": graph_hash,
        "asof": ASOF,
    }


@router.get("/graph/summary")
def get_graph_summary(tenant_id: str = Query("demo-tenant")):
    """Return aggregate counts per node type for a tenant."""
    nodes = [n for n in _GRAPH_NODES.values() if n["tenant_id"] == tenant_id]
    edges = [e for e in _GRAPH_EDGES.values()]

    counts_by_type: Dict[str, int] = defaultdict(int)
    for n in nodes:
        counts_by_type[n["node_type"]] += 1

    edge_counts_by_type: Dict[str, int] = defaultdict(int)
    for e in edges:
        edge_counts_by_type[e["edge_type"]] += 1

    total_hash = _stable_hash({
        "counts": dict(counts_by_type),
        "edge_counts": dict(edge_counts_by_type),
    })

    return {
        "tenant_id": tenant_id,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "counts_by_type": dict(sorted(counts_by_type.items())),
        "edge_counts_by_type": dict(sorted(edge_counts_by_type.items())),
        "node_types": NODE_TYPES,
        "edge_types": EDGE_TYPES,
        "summary_hash": total_hash,
        "asof": ASOF,
    }


@router.post("/graph/nodes")
def add_node(req: AddNodeRequest):
    """Add a node to the evidence graph."""
    if req.node_type not in NODE_TYPES:
        return {"error": f"Unknown node_type: {req.node_type}. Must be one of {NODE_TYPES}"}
    node = {
        "node_id": req.node_id,
        "node_type": req.node_type,
        "label": req.label,
        "tenant_id": req.tenant_id,
        "metadata": req.metadata or {},
    }
    _GRAPH_NODES[req.node_id] = node
    return {"node": node, "status": "added"}


@router.post("/graph/edges")
def add_edge(req: AddEdgeRequest):
    """Add an edge to the evidence graph."""
    if req.edge_type not in EDGE_TYPES:
        return {"error": f"Unknown edge_type: {req.edge_type}. Must be one of {EDGE_TYPES}"}
    edge_id = "e-" + _stable_hash({"src": req.src, "dst": req.dst, "type": req.edge_type})
    edge = {
        "edge_id": edge_id,
        "src": req.src,
        "dst": req.dst,
        "edge_type": req.edge_type,
        "tenant_id": req.tenant_id,
        "metadata": req.metadata or {},
    }
    _GRAPH_EDGES[edge_id] = edge
    return {"edge": edge, "status": "added"}


@router.get("/graph/bfs")
def get_bfs(
    start_id: str = Query(...),
    depth: int = Query(2, ge=1, le=10),
    tenant_id: str = Query("demo-tenant"),
):
    """BFS traversal from start_id up to depth hops. Returns reachable nodes and traversal edges."""
    all_edges = list(_GRAPH_EDGES.values())
    reachable_ids = _bfs(start_id, depth, all_edges)
    nodes = [_GRAPH_NODES[nid] for nid in reachable_ids if nid in _GRAPH_NODES]
    edges = [
        e for e in all_edges
        if e["src"] in reachable_ids and e["dst"] in reachable_ids
    ]
    bfs_hash = _stable_hash({"start_id": start_id, "depth": depth, "nodes": sorted(reachable_ids)})
    return {
        "start_id": start_id,
        "depth": depth,
        "tenant_id": tenant_id,
        "nodes": sorted(nodes, key=lambda n: n["node_id"]),
        "edges": sorted(edges, key=lambda e: e["edge_id"]),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "bfs_hash": bfs_hash,
        "asof": ASOF,
    }
