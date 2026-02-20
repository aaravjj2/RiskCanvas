/**
 * EvidencePage.tsx (v5.54.0 — Wave 65)
 * Route: /evidence
 *
 * Evidence Graph v1 — shows the deterministic entity graph connecting
 * datasets → runs → artifacts → attestations → decisions.
 *
 * data-testids:
 *   evidence-page, evidence-summary-ready, evidence-graph-ready,
 *   evidence-node-{i}, evidence-edge-{i}, evidence-node-drawer,
 *   evidence-type-filter, evidence-node-count, evidence-edge-count
 */
import { useState, useEffect, useCallback } from "react";
import PageShell from "@/components/ui/PageShell";
import RightDrawer from "@/components/ui/RightDrawer";

const API = (path: string) => `/api${path}`;

interface GraphNode {
  node_id: string;
  node_type: string;
  label: string;
  tenant_id: string;
  metadata?: Record<string, unknown>;
}

interface GraphEdge {
  edge_id: string;
  src: string;
  dst: string;
  edge_type: string;
  tenant_id?: string;
}

interface GraphSummary {
  tenant_id: string;
  node_count: number;
  edge_count: number;
  counts_by_type: Record<string, number>;
  edge_counts_by_type: Record<string, number>;
  node_types: string[];
  edge_types: string[];
  summary_hash: string;
  asof: string;
}

interface GraphResponse {
  tenant_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  node_count: number;
  edge_count: number;
  graph_hash: string;
  asof: string;
}

const NODE_TYPE_COLORS: Record<string, string> = {
  dataset:          "bg-blue-900/50 text-blue-300 border-blue-700/50",
  scenario:         "bg-purple-900/50 text-purple-300 border-purple-700/50",
  run:              "bg-green-900/50 text-green-300 border-green-700/50",
  job:              "bg-yellow-900/50 text-yellow-300 border-yellow-700/50",
  artifact:         "bg-orange-900/50 text-orange-300 border-orange-700/50",
  attestation:      "bg-teal-900/50 text-teal-300 border-teal-700/50",
  review:           "bg-pink-900/50 text-pink-300 border-pink-700/50",
  compliance_pack:  "bg-indigo-900/50 text-indigo-300 border-indigo-700/50",
  decision_packet:  "bg-red-900/50 text-red-300 border-red-700/50",
};

const EDGE_TYPE_ICONS: Record<string, string> = {
  created_from:   "→",
  uses:           "⊃",
  produces:       "⇒",
  attests:        "✓",
  approves:       "✅",
  exports:        "↗",
  belongs_to_tenant: "⊂",
};

export default function EvidencePage() {
  const [summary, setSummary] = useState<GraphSummary | null>(null);
  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [expandedTypes, setExpandedTypes] = useState<Set<string>>(new Set());

  const loadAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [sumRes, graphRes] = await Promise.all([
        fetch(API("/evidence/graph/summary")),
        fetch(API("/evidence/graph")),
      ]);
      if (!sumRes.ok) throw new Error("Summary fetch failed");
      if (!graphRes.ok) throw new Error("Graph fetch failed");
      const [sumData, graphData] = await Promise.all([sumRes.json(), graphRes.json()]);
      setSummary(sumData);
      setGraph(graphData);
      // Default: expand all types
      const types = new Set<string>((graphData.nodes as GraphNode[]).map((n) => n.node_type));
      setExpandedTypes(types);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadAll(); }, [loadAll]);

  const displayedNodes = graph?.nodes.filter(n =>
    !typeFilter || n.node_type === typeFilter
  ) ?? [];

  const nodesByType = displayedNodes.reduce<Record<string, GraphNode[]>>((acc, n) => {
    (acc[n.node_type] = acc[n.node_type] || []).push(n);
    return acc;
  }, {});

  // Keyboard nav: ESC closes drawer
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setSelectedNode(null);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  return (
    <PageShell
      title="Evidence Graph"
      subtitle="Wave 65 — v5.54.0"
      statusBar={
        summary && (
          <span className="text-xs text-muted-foreground font-mono">
            hash: {summary.summary_hash} · asof: {summary.asof}
          </span>
        )
      }
      actions={
        <button
          onClick={loadAll}
          className="px-3 py-1.5 text-xs rounded bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 transition"
          data-testid="evidence-refresh-btn"
        >
          Refresh
        </button>
      }
    >
      <div className="space-y-6" data-testid="evidence-page">
        {/* Summary Cards */}
        {loading && (
          <div className="text-sm text-muted-foreground animate-pulse" data-testid="evidence-loading">
            Loading evidence graph…
          </div>
        )}
        {error && (
          <div className="rounded border border-red-700/50 bg-red-900/20 p-4 text-red-300 text-sm" data-testid="evidence-error">
            {error}
          </div>
        )}

        {summary && !loading && (
          <div data-testid="evidence-summary-ready">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
              <div className="rounded border border-border bg-card p-3 text-center">
                <div className="text-2xl font-bold text-primary" data-testid="evidence-node-count">
                  {summary.node_count}
                </div>
                <div className="text-xs text-muted-foreground">Total Nodes</div>
              </div>
              <div className="rounded border border-border bg-card p-3 text-center">
                <div className="text-2xl font-bold text-green-400" data-testid="evidence-edge-count">
                  {summary.edge_count}
                </div>
                <div className="text-xs text-muted-foreground">Total Edges</div>
              </div>
              <div className="rounded border border-border bg-card p-3 text-center">
                <div className="text-2xl font-bold text-purple-400">
                  {Object.keys(summary.counts_by_type).length}
                </div>
                <div className="text-xs text-muted-foreground">Node Types</div>
              </div>
              <div className="rounded border border-border bg-card p-3 text-center">
                <div className="text-2xl font-bold text-teal-400">
                  {Object.keys(summary.edge_counts_by_type).length}
                </div>
                <div className="text-xs text-muted-foreground">Edge Types</div>
              </div>
            </div>

            {/* Type distribution */}
            <div className="flex flex-wrap gap-2 mb-4">
              {Object.entries(summary.counts_by_type).map(([type, count]) => (
                <span
                  key={type}
                  className={`text-xs px-2 py-0.5 rounded-full border font-mono
                    ${NODE_TYPE_COLORS[type] ?? "bg-gray-700 text-gray-300 border-gray-600"}
                    cursor-pointer transition hover:opacity-80
                    ${typeFilter === type ? "ring-2 ring-white/40" : ""}`}
                  onClick={() => setTypeFilter(t => t === type ? "" : type)}
                  data-testid={`evidence-type-chip-${type}`}
                >
                  {type}: {count}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Type filter */}
        {summary && (
          <div className="flex items-center gap-2">
            <label className="text-xs text-muted-foreground">Filter by type:</label>
            <select
              value={typeFilter}
              onChange={e => setTypeFilter(e.target.value)}
              className="text-xs bg-card border border-border rounded px-2 py-1"
              data-testid="evidence-type-filter"
            >
              <option value="">All types</option>
              {(summary.node_types ?? []).map(t => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
            {typeFilter && (
              <button
                onClick={() => setTypeFilter("")}
                className="text-xs text-muted-foreground hover:text-foreground"
              >
                Clear
              </button>
            )}
          </div>
        )}

        {/* Graph list view — grouped by node type */}
        {graph && !loading && (
          <div className="space-y-4" data-testid="evidence-graph-ready">
            {Object.entries(nodesByType).map(([ntype, nodes]) => (
              <div key={ntype} className="rounded border border-border bg-card overflow-hidden">
                <button
                  onClick={() => setExpandedTypes(prev => {
                    const next = new Set(prev);
                    next.has(ntype) ? next.delete(ntype) : next.add(ntype);
                    return next;
                  })}
                  className="w-full flex items-center justify-between px-4 py-2 text-sm font-medium hover:bg-muted/30 transition"
                  data-testid={`evidence-type-section-${ntype}`}
                >
                  <span className={`px-2 py-0.5 rounded-full text-xs border font-mono ${NODE_TYPE_COLORS[ntype] ?? "bg-gray-700 text-gray-300 border-gray-600"}`}>
                    {ntype}
                  </span>
                  <span className="text-xs text-muted-foreground">{nodes.length} nodes {expandedTypes.has(ntype) ? "▾" : "▸"}</span>
                </button>

                {expandedTypes.has(ntype) && (
                  <div className="divide-y divide-border/30">
                    {nodes.map((node, i) => {
                      // Find edges for this node
                      const nodeEdges = graph.edges.filter(
                        e => e.src === node.node_id || e.dst === node.node_id
                      );
                      return (
                        <div
                          key={node.node_id}
                          className="px-4 py-2 hover:bg-muted/20 cursor-pointer transition"
                          onClick={() => setSelectedNode(node)}
                          data-testid={`evidence-node-${i}`}
                          role="button"
                          tabIndex={0}
                          onKeyDown={e => e.key === "Enter" && setSelectedNode(node)}
                        >
                          <div className="flex items-start justify-between">
                            <div>
                              <span className="text-sm text-foreground font-medium">
                                {node.label}
                              </span>
                              <span className="text-xs text-muted-foreground font-mono ml-2">
                                {node.node_id}
                              </span>
                            </div>
                            <span className="text-xs text-muted-foreground ml-4 shrink-0">
                              {nodeEdges.length} edges
                            </span>
                          </div>
                          {nodeEdges.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-1">
                              {nodeEdges.slice(0, 3).map((e, ei) => (
                                <span
                                  key={e.edge_id}
                                  className="text-xs text-muted-foreground font-mono"
                                  data-testid={`evidence-edge-${i}-${ei}`}
                                >
                                  {EDGE_TYPE_ICONS[e.edge_type] ?? "—"} {e.edge_type}
                                  {" → "}
                                  {e.src === node.node_id ? e.dst : e.src}
                                </span>
                              ))}
                              {nodeEdges.length > 3 && (
                                <span className="text-xs text-muted-foreground">+{nodeEdges.length - 3} more</span>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            ))}

            {/* Edges section */}
            <div className="rounded border border-border bg-card overflow-hidden">
              <div className="px-4 py-2 border-b border-border/30 text-sm font-medium text-muted-foreground">
                All Edges ({graph.edges.length})
              </div>
              <div className="divide-y divide-border/30 max-h-64 overflow-y-auto">
                {graph.edges.map((edge, i) => (
                  <div
                    key={edge.edge_id}
                    className="px-4 py-1.5 text-xs font-mono flex items-center gap-2"
                    data-testid={`evidence-edge-${i}`}
                  >
                    <span className="text-muted-foreground">{edge.src}</span>
                    <span className="text-primary">{EDGE_TYPE_ICONS[edge.edge_type] ?? "→"} {edge.edge_type}</span>
                    <span className="text-muted-foreground">{edge.dst}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Node Detail Drawer */}
      <RightDrawer
        open={selectedNode !== null}
        onClose={() => setSelectedNode(null)}
        title={selectedNode?.label ?? "Node Detail"}
      >
        {selectedNode && (
          <div className="space-y-4 p-4" data-testid="evidence-node-drawer">
            <div className="space-y-2">
              <div>
                <span className="text-xs text-muted-foreground">ID</span>
                <p className="text-sm font-mono mt-0.5">{selectedNode.node_id}</p>
              </div>
              <div>
                <span className="text-xs text-muted-foreground">Type</span>
                <p className={`text-sm mt-0.5 inline-block px-2 py-0.5 rounded-full text-xs border font-mono ${NODE_TYPE_COLORS[selectedNode.node_type] ?? "bg-gray-700"}`}>
                  {selectedNode.node_type}
                </p>
              </div>
              <div>
                <span className="text-xs text-muted-foreground">Tenant</span>
                <p className="text-sm font-mono mt-0.5">{selectedNode.tenant_id}</p>
              </div>
            </div>

            {/* Connected edges */}
            <div>
              <h3 className="text-sm font-semibold mb-2">Connections</h3>
              <div className="space-y-1">
                {(graph?.edges ?? [])
                  .filter(e => e.src === selectedNode.node_id || e.dst === selectedNode.node_id)
                  .map(e => (
                    <div
                      key={e.edge_id}
                      className="text-xs font-mono flex items-center gap-2 p-1.5 rounded bg-muted/20"
                    >
                      <span className="text-primary">{EDGE_TYPE_ICONS[e.edge_type] ?? "→"}</span>
                      <span className="text-muted-foreground">{e.edge_type}</span>
                      <span>
                        {e.src === selectedNode.node_id ? `→ ${e.dst}` : `← ${e.src}`}
                      </span>
                    </div>
                  ))}
              </div>
              {(graph?.edges ?? []).filter(e => e.src === selectedNode.node_id || e.dst === selectedNode.node_id).length === 0 && (
                <p className="text-xs text-muted-foreground">No connections</p>
              )}
            </div>

            {/* Jump links */}
            <div>
              <h3 className="text-sm font-semibold mb-2">Jump To</h3>
              <div className="space-y-1">
                {selectedNode.node_type === "dataset" && (
                  <a href="/datasets" className="text-xs text-primary hover:underline block" data-testid="evidence-jump-datasets">
                    → Datasets page
                  </a>
                )}
                {selectedNode.node_type === "scenario" && (
                  <a href="/scenario-composer" className="text-xs text-primary hover:underline block" data-testid="evidence-jump-scenarios">
                    → Scenario Composer
                  </a>
                )}
                {selectedNode.node_type === "run" && (
                  <a href="/history" className="text-xs text-primary hover:underline block" data-testid="evidence-jump-runs">
                    → Run History
                  </a>
                )}
                {selectedNode.node_type === "review" && (
                  <a href="/reviews" className="text-xs text-primary hover:underline block" data-testid="evidence-jump-reviews">
                    → Reviews
                  </a>
                )}
                {selectedNode.node_type === "attestation" && (
                  <a href="/attestations" className="text-xs text-primary hover:underline block" data-testid="evidence-jump-attestations">
                    → Attestations
                  </a>
                )}
              </div>
            </div>
          </div>
        )}
      </RightDrawer>
    </PageShell>
  );
}
