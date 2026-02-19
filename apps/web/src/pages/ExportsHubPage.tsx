/**
 * ExportsHubPage.tsx (v4.80.0 — Wave 34)
 *
 * Browse, verify, and inspect recent export packs.
 * Uses: PageShell, DataTable, RightDrawer, ToastCenter
 *
 * Routes: /exports
 *
 * data-testids:
 *   exports-page, exports-list-ready, export-row-{i}, export-verify-btn-{i},
 *   export-drawer-open-{i}, export-detail-drawer, export-refresh-btn
 */
import { useState, useCallback, useEffect } from "react";
import PageShell from "@/components/ui/PageShell";
import { DataTable, type ColumnDef } from "@/components/ui/DataTable";
import RightDrawer from "@/components/ui/RightDrawer";
import { LoadingSkeleton } from "@/components/ui/LoadingSkeleton";
import { ErrorPanel } from "@/components/ui/ErrorPanel";
import { useToast } from "@/components/ui/ToastCenter";
import { exportsGetRecent, exportsVerify } from "@/lib/api";
import { CheckCircle2, RefreshCw } from "lucide-react";

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
          <button
            data-testid="export-refresh-btn"
            onClick={load}
            className="flex items-center gap-1 px-3 py-1.5 text-sm border border-border rounded-md hover:bg-muted"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
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
      </PageShell>

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
