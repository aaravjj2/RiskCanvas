/**
 * ArtifactsPage.tsx (v5.04.0 — Wave 42)
 * Route: /artifacts
 * data-testids: artifacts-page, artifact-row-{i}, artifact-drawer-ready, artifact-verify-btn
 */
import { useState, useCallback, useEffect } from "react";
import PageShell from "@/components/ui/PageShell";
import { DataTable, type ColumnDef } from "@/components/ui/DataTable";
import RightDrawer from "@/components/ui/RightDrawer";
import { useToast } from "@/components/ui/ToastCenter";
import EvidenceBadge from "@/components/ui/EvidenceBadge";

const API = (path: string) => `/api${path}`;

interface Artifact { artifact_id: string; type: string; created_by: string; source_job_id: string; size: number; sha256: string; created_at: string; verified: boolean; manifest?: { files?: string[] }; [key: string]: unknown; }
interface DownloadDescriptor { descriptor_id: string; url: string; sha256: string; size: number; note: string; }

export default function ArtifactsPage() {
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [selected, setSelected] = useState<Artifact | null>(null);
  const [download, setDownload] = useState<DownloadDescriptor | null>(null);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const { addToast } = useToast();

  const load = useCallback(async () => {
    setLoading(true);
    try { const r = await fetch(API("/artifacts")); const d = await r.json(); setArtifacts(d.artifacts ?? []); }
    catch { addToast("Failed to load artifacts", "error"); }
    setLoading(false);
  }, [addToast]);

  useEffect(() => { load(); }, [load]);

  async function openArtifact(art: Artifact) {
    setSelected(art); setDownload(null);
    try { const r = await fetch(API(`/artifacts/${art.artifact_id}/downloads`)); setDownload(await r.json()); } catch {}
  }

  async function handleVerify() {
    if (!selected) return; setVerifying(true);
    try {
      const r = await fetch(API(`/artifacts/${selected.artifact_id}`)); const d = await r.json();
      const ok = d.sha256 === selected.sha256;
      addToast(ok ? "Artifact integrity verified \u2713" : "Hash mismatch \u2014 integrity check FAILED", ok ? "success" : "error");
    } catch { addToast("Verification request failed", "error"); }
    setVerifying(false);
  }

  const columns: ColumnDef<Artifact>[] = [
    { key: "type", header: "Type", sortable: true, width: "w-40" },
    { key: "created_by", header: "Created By", sortable: true, width: "w-28" },
    { key: "size", header: "Size", sortable: true, width: "w-20", render: (r: Artifact) => `${(Number(r.size)/1024).toFixed(1)} KB` },
    { key: "sha256", header: "SHA-256", width: "w-44", render: (r: Artifact) => <EvidenceBadge hash={r.sha256} verified={r.verified} /> },
    { key: "created_at", header: "Created", width: "w-40" },
    { key: "_actions", header: "", width: "w-24",
      render: (row: Artifact, i: number) => (
        <button data-testid={`artifact-row-${i}`} onClick={() => openArtifact(row)}
          className="text-xs px-2 py-0.5 rounded border border-gray-600 hover:bg-gray-700">Details</button>
      ),
    },
  ];

  return (
    <PageShell title="Artifact Registry" subtitle="Signed, verifiable artifacts from jobs and evaluations">
      <div data-testid="artifacts-page" className="space-y-4">
        <div className="flex justify-end"><span className="text-xs text-gray-400">{artifacts.length} artifact{artifacts.length !== 1 ? "s" : ""}</span></div>
        {!loading && <DataTable<Artifact> columns={columns} data={artifacts} rowKey="artifact_id" emptyLabel="No artifacts" />}
      </div>
      <RightDrawer open={!!selected} onClose={() => { setSelected(null); setDownload(null); }} title={selected?.type ?? "Artifact Detail"}>
        {selected && (
          <div data-testid="artifact-drawer-ready" className="space-y-4 text-sm">
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Artifact ID</p><p className="font-mono text-xs break-all text-gray-300">{selected.artifact_id}</p></div>
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Integrity (SHA-256)</p><EvidenceBadge hash={selected.sha256} verified={selected.verified} /></div>
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Created by</p><p className="text-gray-200">{selected.created_by}</p></div>
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Source Job</p><p className="font-mono text-xs text-gray-300">{selected.source_job_id}</p></div>
            {Array.isArray(selected.manifest?.files) && (
              <div>
                <p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Manifest ({selected.manifest!.files!.length} files)</p>
                <ul className="list-disc list-inside space-y-0.5 text-xs text-gray-400">{selected.manifest!.files!.map((f: string) => <li key={f}>{f}</li>)}</ul>
              </div>
            )}
            {download && (
              <div className="rounded bg-gray-800 p-3 space-y-1">
                <p className="text-xs text-gray-400 font-semibold">Download Descriptor</p>
                <p className="text-xs text-gray-300 font-mono">{download.url}</p>
                <p className="text-xs text-gray-400">{download.note}</p>
              </div>
            )}
            <button data-testid="artifact-verify-btn" disabled={verifying} onClick={handleVerify}
              className="w-full rounded bg-emerald-700 py-2 text-sm font-semibold text-white hover:bg-emerald-600 disabled:opacity-40">
              {verifying ? "Verifying\u2026" : "Verify Integrity"}
            </button>
          </div>
        )}
      </RightDrawer>
    </PageShell>
  );
}
