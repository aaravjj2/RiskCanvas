/**
 * EvidenceBar.tsx (v5.58.0 — Wave 69)
 *
 * Global header overlay bar showing live evidence chain status:
 * - Tenant ID
 * - Audit chain head (latest attestation hash)
 * - Graph summary hash
 * - Live refresh every 60s
 *
 * data-testids:
 *   evidence-bar, evidence-bar-tenant, evidence-bar-chain-head,
 *   evidence-bar-graph-hash, evidence-bar-refresh
 */
import { useState, useEffect, useCallback } from "react";

const API = (path: string) => `/api${path}`;

interface GraphSummary {
  tenant_id: string;
  node_count: number;
  edge_count: number;
  summary_hash: string;
  asof: string;
}

interface AttestationSummary {
  chain_head?: string;
  count?: number;
}

function truncate(s: string, n = 12) {
  return s.length > n ? s.slice(0, n) + "…" : s;
}

export default function EvidenceBar() {
  const [summary, setSummary] = useState<GraphSummary | null>(null);
  const [chainHead, setChainHead] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [sumRes, attRes] = await Promise.all([
        fetch(API("/evidence/graph/summary")),
        fetch(API("/attestations")).catch(() => null),
      ]);
      if (sumRes.ok) setSummary(await sumRes.json());
      if (attRes?.ok) {
        const att = await attRes.json() as AttestationSummary;
        if (att.chain_head) setChainHead(att.chain_head);
      }
    } catch {
      // silently fail — EvidenceBar is informational only
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 60_000);
    return () => clearInterval(interval);
  }, [refresh]);

  return (
    <div
      className="w-full flex items-center gap-4 px-4 py-1.5 text-xs font-mono bg-primary/5 border-b border-border/30"
      data-testid="evidence-bar"
    >
      <span className="text-muted-foreground shrink-0">↳ tenant:</span>
      <span className="text-primary font-medium" data-testid="evidence-bar-tenant">
        {summary?.tenant_id ?? "—"}
      </span>

      <span className="text-muted-foreground shrink-0">graph:</span>
      <span
        className="text-teal-400"
        title={summary?.summary_hash ?? ""}
        data-testid="evidence-bar-graph-hash"
      >
        {summary ? truncate(summary.summary_hash, 16) : "loading…"}
      </span>

      {summary && (
        <span className="text-muted-foreground shrink-0">
          {summary.node_count}N/{summary.edge_count}E
        </span>
      )}

      {chainHead && (
        <>
          <span className="text-muted-foreground shrink-0">chain:</span>
          <span
            className="text-green-400"
            title={chainHead}
            data-testid="evidence-bar-chain-head"
          >
            {truncate(chainHead, 16)}
          </span>
        </>
      )}

      {summary && (
        <span className="text-muted-foreground shrink-0 ml-1">
          @{summary.asof.slice(11, 19)}
        </span>
      )}

      <button
        onClick={refresh}
        className="ml-auto text-muted-foreground hover:text-foreground transition"
        title="Refresh evidence bar"
        data-testid="evidence-bar-refresh"
        disabled={loading}
      >
        {loading ? "⟳" : "↺"}
      </button>
    </div>
  );
}
