/**
 * ExportsHubPage.tsx (v5.54.0 — Wave 34 + Decision Packet Generation)
 *
 * Browse, verify, and inspect recent export packs.
 * v5.54.0: Added decision packet generation — POST /exports/decision-packet
 * Uses: PageShell, DataTable, RightDrawer, ToastCenter
 *
 * Routes: /exports
 *
 * data-testids:
 *   exports-page, exports-list-ready, export-row-{i}, export-verify-btn-{i},
 *   export-drawer-open-{i}, export-detail-drawer, export-refresh-btn,
 *   export-generate-packet-btn, export-generate-packet-form,
 *   export-subject-type-select, export-subject-id-input,
 *   export-packet-hash, export-packet-verify-status
 */
import { useState, useCallback, useEffect } from "react";
import PageShell from "@/components/ui/PageShell";
import { DataTable, type ColumnDef } from "@/components/ui/DataTable";
import RightDrawer from "@/components/ui/RightDrawer";
import { LoadingSkeleton } from "@/components/ui/LoadingSkeleton";
import { ErrorPanel } from "@/components/ui/ErrorPanel";
import { useToast } from "@/components/ui/ToastCenter";
import { exportsGetRecent, exportsVerify, exportsGenerateDecisionPacket, exportsVerifyDecisionPacket } from "@/lib/api";
import { CheckCircle2, RefreshCw, FilePlus2 } from "lucide-react";

interface PackRow {
  pack_id: string;
  type: string;
  label: string;
  created_at: string;
  sha256: string;
  size_bytes: number;
  status: string;
  wave: string;
  [key: string]: unknown;
}

const COLUMNS: ColumnDef<PackRow>[] = [
  { key: "label", header: "Pack", sortable: true },
  { key: "type", header: "Type", sortable: true, width: "w-28" },
  { key: "wave", header: "Wave", sortable: true, width: "w-16" },
  { key: "size_bytes", header: "Size", sortable: true, width: "w-24",
    render: (r: PackRow) => `${(Number(r.size_bytes) / 1024).toFixed(1)} KB` },
  { key: "status", header: "Status", width: "w-24",
    render: (r) => (
      <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${
        r.status === "verified" ? "bg-green-100 text-green-700" : "bg-yellow-100 text-yellow-700"
      }`}>
        {r.status === "verified" && <CheckCircle2 className="h-3 w-3" />}
        {String(r.status)}
      </span>
    )},
  { key: "sha256", header: "SHA-256 (prefix)", width: "w-40",
    render: (r) => (
      <span className="font-mono text-xs text-muted-foreground">
        {String(r.sha256).slice(0, 16)}…
      </span>
    )},
];

export default function ExportsHubPage() {
  const [packs, setPacks] = useState<PackRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [drawerPack, setDrawerPack] = useState<PackRow | null>(null);
  const [verifying, setVerifying] = useState<string | null>(null);
  const { addToast } = useToast();

  // Decision packet generation (v5.54.0)
  const [generateOpen, setGenerateOpen] = useState(false);
  const [genSubjectType, setGenSubjectType] = useState("dataset");
  const [genSubjectId, setGenSubjectId] = useState("demo-dataset-001");
  const [genRequestedBy, setGenRequestedBy] = useState("demo@riskcanvas.io");
  const [generating, setGenerating] = useState(false);
  const [lastPacket, setLastPacket] = useState<Record<string, unknown> | null>(null);
  const [verifyingPacket, setVerifyingPacket] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await exportsGetRecent();
      if (data) setPacks(data.packs ?? []);
    } catch {
      setError("Failed to load export packs");
    }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleVerify = useCallback(async (pack: PackRow) => {
    setVerifying(pack.pack_id);
    const data = await exportsVerify(pack.pack_id);
    setVerifying(null);
    if (data?.verified) {
      addToast(`Pack ${pack.pack_id} verified ✓`, "success");
    } else {
      addToast(`Verification failed for ${pack.pack_id}`, "error");
    }
  }, [addToast]);

  async function handleGeneratePacket() {
    if (!genSubjectId.trim()) { addToast("Subject ID required", "error"); return; }
    setGenerating(true);
    try {
      const data = await exportsGenerateDecisionPacket(genSubjectType, genSubjectId, genRequestedBy);
      if (data?.packet) {
        setLastPacket(data.packet);
        setGenerateOpen(false);
        addToast(`Decision packet generated — ${String(data.packet.manifest_hash ?? "").slice(0, 12)}…`, "success");
        await load();
      } else {
        addToast("Generation failed", "error");
      }
    } catch { addToast("Network error", "error"); }
    setGenerating(false);
  }

  async function handleVerifyLastPacket() {
    if (!lastPacket?.packet_id) return;
    setVerifyingPacket(true);
    try {
      const data = await exportsVerifyDecisionPacket(lastPacket.packet_id as string);
      if (data?.verified) {
        setLastPacket(prev => prev ? { ...prev, verify_status: "PASS" } : prev);
        addToast("Packet verification PASS ✓", "success");
      } else {
        setLastPacket(prev => prev ? { ...prev, verify_status: "FAIL" } : prev);
        addToast("Packet verification FAIL", "error");
      }
    } catch { addToast("Verify error", "error"); }
    setVerifyingPacket(false);
  }

  const columnsWithActions: ColumnDef<PackRow>[] = [
    ...COLUMNS,
    {
      key: "_actions",
      header: "Actions",
      width: "w-48",
      render: (row, _i) => (
        <div className="flex items-center gap-1">
          <button
            data-testid={`export-verify-btn-${_i}`}
            onClick={() => handleVerify(row)}
            disabled={verifying === row.pack_id}
            className="px-2 py-0.5 text-xs border border-border rounded hover:bg-muted disabled:opacity-40"
          >
            {verifying === row.pack_id ? "Verifying…" : "Verify"}
          </button>
          <button
            data-testid={`export-drawer-open-${_i}`}
            onClick={() => setDrawerPack(row)}
            className="px-2 py-0.5 text-xs border border-border rounded hover:bg-muted"
          >
            Details
          </button>
        </div>
      ),
    },
  ];

  return (
    <div data-testid="exports-page" className="p-6 max-w-6xl mx-auto">
      <PageShell
        title="Exports Hub"
        subtitle="Wave 34 · v4.80.0 — Browse and verify recent export packs"
        actions={
          <div className="flex items-center gap-2">
            <button
              data-testid="export-generate-packet-btn"
              onClick={() => setGenerateOpen(true)}
              className="flex items-center gap-1 px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
            >
              <FilePlus2 className="h-4 w-4" />
              Generate Packet
            </button>
            <button
              data-testid="export-refresh-btn"
              onClick={load}
              className="flex items-center gap-1 px-3 py-1.5 text-sm border border-border rounded-md hover:bg-muted"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </button>
          </div>
        }
        statusBar={<>DEMO mode · {packs.length} packs loaded · deterministic fixtures</>}
      >
        {loading && <LoadingSkeleton rows={5} />}
        {error && <ErrorPanel message={error} onRetry={load} />}
        {!loading && !error && (
          <div data-testid="exports-list-ready">
            <DataTable<PackRow>
              columns={columnsWithActions}
              data={packs.map((p, i) => ({
                ...p,
                "data-testid": `export-row-${i}`,
              }))}
              rowKey="pack_id"
              selectable
              bulkActionLabel="Export selected packs"
              emptyLabel="No export packs available"
            />
          </div>
        )}
        {lastPacket && (
          <div
            data-testid="export-last-packet"
            className="mt-4 p-4 border border-border rounded-md bg-muted/40 flex flex-col gap-2 text-sm"
          >
            <p className="font-medium">Last Generated Packet</p>
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">Manifest Hash:</span>
              <span
                data-testid="export-packet-hash"
                data-hash={lastPacket.manifest_hash}
                className="font-mono text-xs break-all"
              >
                {String(lastPacket.manifest_hash).slice(0, 16)}…
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                data-testid="export-packet-verify-btn"
                onClick={handleVerifyLastPacket}
                disabled={verifyingPacket}
                className="px-3 py-1 text-xs border border-border rounded-md hover:bg-muted disabled:opacity-50"
              >
                {verifyingPacket ? "Verifying…" : "Verify Hash"}
              </button>
              {!!(lastPacket.verify_status as string) && (
                <span
                  data-testid="export-packet-verify-status"
                  className={(lastPacket.verify_status as string) === "PASS" ? "text-green-600 font-medium" : "text-red-600 font-medium"}
                >
                  {(lastPacket.verify_status as string) === "PASS" ? "✓ PASS" : "✗ FAIL"}
                </span>
              )}
            </div>
          </div>
        )}
      </PageShell>

      {/* Generate Packet drawer */}
      <RightDrawer
        open={generateOpen}
        onClose={() => setGenerateOpen(false)}
        title="Generate Decision Packet"
      >
        <div data-testid="export-generate-packet-form" className="flex flex-col gap-4 text-sm">
          <div className="flex flex-col gap-1.5">
            <label className="font-medium text-muted-foreground">Subject Type</label>
            <select
              data-testid="export-subject-type-select"
              value={genSubjectType}
              onChange={e => setGenSubjectType(e.target.value)}
              className="border border-border rounded-md px-2 py-1.5 bg-background text-sm"
            >
              <option value="dataset">Dataset</option>
              <option value="scenario">Scenario</option>
              <option value="review">Review</option>
            </select>
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="font-medium text-muted-foreground">Subject ID</label>
            <input
              data-testid="export-subject-id-input"
              type="text"
              value={genSubjectId}
              onChange={e => setGenSubjectId(e.target.value)}
              placeholder="e.g. demo-dataset-001"
              className="border border-border rounded-md px-2 py-1.5 bg-background text-sm font-mono"
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="font-medium text-muted-foreground">Requested By</label>
            <input
              data-testid="export-requested-by-input"
              type="text"
              value={genRequestedBy}
              onChange={e => setGenRequestedBy(e.target.value)}
              placeholder="e.g. judge@riskcanvas.io"
              className="border border-border rounded-md px-2 py-1.5 bg-background text-sm"
            />
          </div>
          <button
            data-testid="export-generate-packet-submit-btn"
            onClick={handleGeneratePacket}
            disabled={generating || !genSubjectId.trim()}
            className="w-full px-3 py-2 text-sm bg-primary text-primary-foreground rounded-md disabled:opacity-50"
          >
            <FilePlus2 className="h-4 w-4 inline mr-1" />
            {generating ? "Generating…" : "Generate Packet"}
          </button>
        </div>
      </RightDrawer>

      {/* Detail drawer */}
      <RightDrawer
        open={drawerPack !== null}
        onClose={() => setDrawerPack(null)}
        title={drawerPack?.label ?? "Pack Details"}
      >
        {drawerPack && (
          <div className="flex flex-col gap-4 text-sm">
            <div className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1.5">
              {[
                ["Pack ID", drawerPack.pack_id],
                ["Type", drawerPack.type],
                ["Wave", drawerPack.wave],
                ["Status", drawerPack.status],
                ["Created", drawerPack.created_at],
                ["Size", `${(drawerPack.size_bytes / 1024).toFixed(1)} KB`],
              ].map(([k, v]) => (
                <><dt key={`k-${k}`} className="font-medium text-muted-foreground">{k}</dt>
                  <dd key={`v-${k}`} className="font-mono text-xs break-all">{v}</dd></>
              ))}
            </div>
            <div>
              <p className="font-medium text-muted-foreground mb-1">SHA-256</p>
              <p
                data-testid="export-drawer-sha256"
                className="font-mono text-xs break-all bg-muted px-2 py-1.5 rounded"
              >
                {drawerPack.sha256}
              </p>
            </div>
            <button
              data-testid="export-drawer-verify-btn"
              onClick={async () => {
                const d = await exportsVerify(drawerPack.pack_id);
                addToast(d?.verified ? "Verified ✓" : "Verification failed", d?.verified ? "success" : "error");
              }}
              className="w-full px-3 py-2 text-sm bg-primary text-primary-foreground rounded-md"
            >
              <CheckCircle2 className="h-4 w-4 inline mr-1" />
              Verify Pack
            </button>
          </div>
        )}
      </RightDrawer>
    </div>
  );
}
