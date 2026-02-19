/**
 * AttestationsPage.tsx (v5.08.0 — Wave 43)
 * Route: /attestations
 * data-testids: attestations-page, attestation-row-{i}, attestation-drawer-ready, attestation-prev-link
 */
import { useState, useCallback, useEffect } from "react";
import PageShell from "@/components/ui/PageShell";
import { DataTable, type ColumnDef } from "@/components/ui/DataTable";
import RightDrawer from "@/components/ui/RightDrawer";
import { useToast } from "@/components/ui/ToastCenter";
import EvidenceBadge from "@/components/ui/EvidenceBadge";

const API = (path: string) => `/api${path}`;

interface Attestation { attestation_id: string; tenant_id: string; subject: string; statement_type: string; issued_by: string; issued_at: string; input_hash: string; output_hash: string; prev_hash: string; seq: number; [key: string]: unknown; }

const STMT_COLOR: Record<string, string> = {
  "mr-review-complete": "bg-blue-900/30 text-blue-300",
  "incident-run-complete": "bg-red-900/30 text-red-300",
  "readiness-eval-complete": "bg-green-900/30 text-green-300",
  "artifact-created": "bg-teal-900/30 text-teal-300",
};

export default function AttestationsPage() {
  const [attestations, setAttestations] = useState<Attestation[]>([]);
  const [chainHead, setChainHead] = useState<string>("");
  const [selected, setSelected] = useState<Attestation | null>(null);
  const [loading, setLoading] = useState(true);
  const { addToast } = useToast();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch(API("/attestations"));
      const d = await r.json();
      setAttestations(d.attestations ?? []);
      setChainHead(d.chain_head ?? "");
    } catch { addToast("Failed to load attestations", "error"); }
    setLoading(false);
  }, [addToast]);

  useEffect(() => { load(); }, [load]);

  async function navigateToPrev(prevId: string) {
    try { const r = await fetch(API(`/attestations/${prevId}`)); setSelected(await r.json()); }
    catch { addToast("Could not load previous attestation", "error"); }
  }

  const columns: ColumnDef<Attestation>[] = [
    { key: "seq", header: "#", width: "w-10", sortable: true, render: (r: Attestation) => <span className="text-xs text-gray-400">#{r.seq}</span> },
    { key: "statement_type", header: "Statement", sortable: true,
      render: (r: Attestation) => <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${STMT_COLOR[r.statement_type] ?? "bg-gray-700 text-gray-300"}`}>{r.statement_type}</span>
    },
    { key: "issued_by", header: "Issued By", sortable: true, width: "w-28" },
    { key: "output_hash", header: "Output Hash", width: "w-44", render: (r: Attestation) => <EvidenceBadge hash={r.output_hash} verified /> },
    { key: "issued_at", header: "Issued At", sortable: true, width: "w-40" },
    { key: "_actions", header: "", width: "w-20",
      render: (row: Attestation, i: number) => (
        <button data-testid={`attestation-row-${i}`} onClick={() => setSelected(row)}
          className="text-xs px-2 py-0.5 rounded border border-gray-600 hover:bg-gray-700">Details</button>
      ),
    },
  ];

  return (
    <PageShell title="Attestations" subtitle="Cryptographic action receipts — tamper-evident hash chain">
      <div data-testid="attestations-page" className="space-y-4">
        {chainHead && (
          <div className="rounded border border-gray-700 bg-gray-800/50 p-3">
            <p className="text-xs text-gray-400 mb-1">Chain Head</p>
            <EvidenceBadge hash={chainHead} verified label="Chain Head" />
          </div>
        )}
        {!loading && <DataTable<Attestation> columns={columns} data={attestations} rowKey="attestation_id" emptyLabel="No attestations" />}
      </div>
      <RightDrawer open={!!selected} onClose={() => setSelected(null)} title={selected?.statement_type ?? "Attestation Detail"}>
        {selected && (
          <div data-testid="attestation-drawer-ready" className="space-y-4 text-sm">
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Attestation ID</p><p className="font-mono text-xs break-all text-gray-300">{selected.attestation_id}</p></div>
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Subject</p><p className="font-mono text-xs break-all text-gray-300">{selected.subject}</p></div>
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Statement</p><span className={`text-xs font-medium px-2 py-0.5 rounded-full ${STMT_COLOR[selected.statement_type] ?? "bg-gray-700 text-gray-300"}`}>{selected.statement_type}</span></div>
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Input Hash</p><EvidenceBadge hash={selected.input_hash} verified label="Input" /></div>
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Output Hash</p><EvidenceBadge hash={selected.output_hash} verified label="Output" /></div>
            <div>
              <p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Previous Attestation</p>
              {selected.prev_hash === "genesis"
                ? <span className="text-xs text-gray-400 italic">genesis (chain root)</span>
                : <button data-testid="attestation-prev-link" onClick={() => navigateToPrev(selected.prev_hash)}
                    className="font-mono text-xs text-blue-400 underline hover:text-blue-300 break-all text-left">{selected.prev_hash}</button>
              }
            </div>
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Issued By / At</p><p className="text-gray-200">{selected.issued_by} · {selected.issued_at}</p></div>
          </div>
        )}
      </RightDrawer>
    </PageShell>
  );
}
