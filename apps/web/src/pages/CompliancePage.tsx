/**
 * CompliancePage.tsx (v5.11.0 — Wave 44)
 * Route: /compliance
 * data-testids: compliance-page, compliance-generate-btn, compliance-packs-ready, compliance-pack-row-{i}, compliance-verify-btn
 */
import { useState, useCallback, useEffect } from "react";
import PageShell from "@/components/ui/PageShell";
import { DataTable, type ColumnDef } from "@/components/ui/DataTable";
import RightDrawer from "@/components/ui/RightDrawer";
import { useToast } from "@/components/ui/ToastCenter";
import EvidenceBadge from "@/components/ui/EvidenceBadge";

const API = (path: string) => `/api${path}`;

interface CompliancePack { pack_id: string; tenant_id: string; tenant_name: string; window: string; generated_at: string; file_count: number; manifest_hash: string; controls_evaluated: number; controls_passed: number; verdict: string; files?: Array<{ name: string; sha256: string }>; [key: string]: unknown; }

export default function CompliancePage() {
  const [packs, setPacks] = useState<CompliancePack[]>([]);
  const [selected, setSelected] = useState<CompliancePack | null>(null);
  const [generating, setGenerating] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [loading, setLoading] = useState(true);
  const { addToast } = useToast();

  const loadPacks = useCallback(async () => {
    setLoading(true);
    try { const r = await fetch(API("/compliance/packs")); if (r.ok) { const d = await r.json(); setPacks(d.packs ?? []); } }
    catch {}
    setLoading(false);
  }, []);

  useEffect(() => { loadPacks(); }, [loadPacks]);

  async function handleGenerate() {
    setGenerating(true);
    try {
      const r = await fetch(API("/compliance/generate-pack"), { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ window: "last_30_demo_days" }) });
      const d = await r.json();
      if (r.ok) { addToast(`Pack generated — verdict: ${d.verdict}`, "success"); await loadPacks(); setSelected(d); }
      else { addToast(d.detail ?? "Generation failed", "error"); }
    } catch { addToast("Network error", "error"); }
    setGenerating(false);
  }

  async function handleVerify() {
    if (!selected) return; setVerifying(true);
    try {
      const r = await fetch(API(`/compliance/packs/${selected.pack_id}/verify`), { method: "POST" });
      const d = await r.json();
      addToast(d.verified ? "Compliance pack verified \u2713" : "Verification FAILED \u2014 manifest mismatch", d.verified ? "success" : "error");
    } catch { addToast("Verification request failed", "error"); }
    setVerifying(false);
  }

  const columns: ColumnDef<CompliancePack>[] = [
    { key: "tenant_name", header: "Tenant", sortable: true },
    { key: "window", header: "Window", sortable: true, width: "w-44" },
    { key: "file_count", header: "Files", width: "w-16" },
    { key: "verdict", header: "Verdict", width: "w-24",
      render: (r: CompliancePack) => <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${r.verdict==="PASS"?"bg-green-900/40 text-green-300":"bg-red-900/40 text-red-300"}`}>{r.verdict}</span>
    },
    { key: "manifest_hash", header: "Manifest Hash", width: "w-44",
      render: (r: CompliancePack) => <EvidenceBadge hash={r.manifest_hash} verified={r.verdict==="PASS"} label="Manifest" />
    },
    { key: "generated_at", header: "Generated", sortable: true, width: "w-44" },
    { key: "_actions", header: "", width: "w-24",
      render: (row: CompliancePack, i: number) => (
        <button data-testid={`compliance-pack-row-${i}`} onClick={() => setSelected(row)}
          className="text-xs px-2 py-0.5 rounded border border-gray-600 hover:bg-gray-700">Details</button>
      ),
    },
  ];

  return (
    <PageShell title="Compliance" subtitle="SOC2-ish evidence pack generator — one-click, deterministic">
      <div data-testid="compliance-page" className="space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-400">Generate a tamper-evident compliance evidence pack for your tenant.</p>
          <button data-testid="compliance-generate-btn" disabled={generating} onClick={handleGenerate}
            className="rounded bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-40">
            {generating ? "Generating\u2026" : "Generate Pack"}
          </button>
        </div>
        {!loading && packs.length === 0 && <div className="text-center py-12 text-gray-500 text-sm">No packs yet. Click <strong>Generate Pack</strong> to create one.</div>}
        {packs.length > 0 && <DataTable<CompliancePack> data-testid="compliance-packs-ready" columns={columns} data={packs} rowKey="pack_id" emptyLabel="No compliance packs" />}
      </div>
      <RightDrawer open={!!selected} onClose={() => setSelected(null)} title="Compliance Pack Detail">
        {selected && (
          <div className="space-y-4 text-sm">
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Pack ID</p><p className="font-mono text-xs break-all text-gray-300">{selected.pack_id}</p></div>
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Tenant</p><p className="text-gray-200">{selected.tenant_name}</p></div>
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Window</p><p className="text-gray-200">{selected.window}</p></div>
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Controls</p><p className="text-gray-200">{selected.controls_passed}/{selected.controls_evaluated} passed</p></div>
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Manifest Hash</p><EvidenceBadge hash={selected.manifest_hash} verified={selected.verdict==="PASS"} label="Manifest" /></div>
            {selected.files && (
              <div>
                <p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Files ({selected.files.length})</p>
                <ul className="space-y-1">{selected.files.map(f => <li key={f.name} className="flex items-center justify-between text-xs"><span className="text-gray-300">{f.name}</span><EvidenceBadge hash={f.sha256} verified label={f.name} /></li>)}</ul>
              </div>
            )}
            <button data-testid="compliance-verify-btn" disabled={verifying} onClick={handleVerify}
              className="w-full rounded bg-emerald-700 py-2 text-sm font-semibold text-white hover:bg-emerald-600 disabled:opacity-40">
              {verifying ? "Verifying\u2026" : "Verify Pack"}
            </button>
          </div>
        )}
      </RightDrawer>
    </PageShell>
  );
}
