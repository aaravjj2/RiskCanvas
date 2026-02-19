/**
 * AdminPage.tsx (v5.01.0 — Wave 41)
 *
 * Route: /admin
 * data-testids: admin-page, tenants-table-ready, tenant-row-{i},
 *   members-table-ready, member-row-{i}, invite-btn,
 *   admin-audit-tab, audit-list-ready, audit-row-{i}
 */
import { useState, useCallback, useEffect } from "react";
import PageShell from "@/components/ui/PageShell";
import { DataTable, type ColumnDef } from "@/components/ui/DataTable";
import RightDrawer from "@/components/ui/RightDrawer";
import { useToast } from "@/components/ui/ToastCenter";
import PermissionBadge from "@/components/ui/PermissionBadge";

const API = (path: string) => `/api${path}`;

interface Tenant { tenant_id: string; name: string; slug: string; member_count: number; created_at: string; [key: string]: unknown; }
interface Member { membership_id: string; user_id: string; tenant_id: string; email: string; display_name: string; role: string; joined_at: string; [key: string]: unknown; }
interface AuditEvent { action: string; actor?: string; created_at?: string; resource_type?: string; [key: string]: unknown; }

const ROLE_PERMS: Record<string, string[]> = {
  OWNER: ["tenant.read","tenant.write","audit.read","policy.write","exports.write","jobs.write","admin.read","admin.write","artifacts.read","artifacts.write","attestations.read","compliance.write"],
  ADMIN: ["tenant.read","audit.read","policy.write","exports.write","jobs.write","admin.read","artifacts.read","artifacts.write","attestations.read","compliance.write"],
  ANALYST: ["tenant.read","audit.read","exports.write","jobs.write","artifacts.read","attestations.read"],
  VIEWER: ["tenant.read","audit.read","artifacts.read","attestations.read"],
};

type AdminTab = "tenants" | "audit";

export default function AdminPage() {
  const [tab, setTab] = useState<AdminTab>("tenants");
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null);
  const [selectedMember, setSelectedMember] = useState<Member | null>(null);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("ANALYST");
  const [inviting, setInviting] = useState(false);
  const [loading, setLoading] = useState(true);
  const { addToast } = useToast();

  const loadTenants = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch(API("/tenants"), { headers: { "x-demo-role": "OWNER" } });
      const d = await r.json();
      const ts: Tenant[] = d.tenants ?? [];
      setTenants(ts);
      if (ts.length > 0) setSelectedTenant(t => t ?? ts[0]);
    } catch { addToast("Failed to load tenants", "error"); }
    setLoading(false);
  }, []); // eslint-disable-line

  const loadMembers = useCallback(async (tid: string) => {
    try {
      const r = await fetch(API(`/tenants/${tid}/members`), { headers: { "x-demo-role": "OWNER" } });
      const d = await r.json();
      setMembers(d.members ?? []);
    } catch { addToast("Failed to load members", "error"); }
  }, [addToast]);

  const loadAudit = useCallback(async () => {
    try {
      const r = await fetch(API("/audit/v2?limit=50"));
      if (r.ok) { const d = await r.json(); setAuditEvents(d.events ?? d.audit_events ?? []); }
    } catch { /* optional */ }
  }, []);

  useEffect(() => { loadTenants(); loadAudit(); }, []); // eslint-disable-line
  useEffect(() => { if (selectedTenant) loadMembers(selectedTenant.tenant_id); }, [selectedTenant]); // eslint-disable-line

  async function handleInvite() {
    if (!selectedTenant || !inviteEmail) return;
    setInviting(true);
    try {
      const r = await fetch(API(`/tenants/${selectedTenant.tenant_id}/members`), {
        method: "POST", headers: { "content-type": "application/json", "x-demo-role": "OWNER" },
        body: JSON.stringify({ email: inviteEmail, role: inviteRole }),
      });
      if (r.ok) {
        addToast(`Invited ${inviteEmail} as ${inviteRole}`, "success");
        setInviteEmail(""); await loadMembers(selectedTenant.tenant_id); await loadTenants();
      } else { const e = await r.json(); addToast(e.detail ?? "Invite failed", "error"); }
    } catch { addToast("Network error", "error"); }
    setInviting(false);
  }

  const tenantCols: ColumnDef<Tenant>[] = [
    { key: "name", header: "Tenant", sortable: true },
    { key: "slug", header: "Slug", width: "w-36" },
    { key: "member_count", header: "Members", width: "w-20" },
    { key: "_actions", header: "", width: "w-20",
      render: (row: Tenant, i: number) => (
        <button data-testid={`tenant-row-${i}`} onClick={() => setSelectedTenant(row)}
          className="text-xs px-2 py-0.5 rounded border border-gray-600 hover:bg-gray-700 text-blue-300">
          Select
        </button>
      ),
    },
  ];

  const memberCols: ColumnDef<Member>[] = [
    { key: "display_name", header: "Name", sortable: true },
    { key: "email", header: "Email", sortable: true },
    { key: "role", header: "Role", width: "w-24",
      render: (r: Member) => (
        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
          r.role==="OWNER"?"bg-yellow-800/50 text-yellow-300":r.role==="ADMIN"?"bg-blue-800/50 text-blue-300":
          r.role==="ANALYST"?"bg-teal-800/50 text-teal-300":"bg-gray-700 text-gray-400"}`}>{r.role}</span>
      ),
    },
    { key: "joined_at", header: "Joined", width: "w-36" },
    { key: "_actions", header: "", width: "w-20",
      render: (row: Member, i: number) => (
        <button data-testid={`member-row-${i}`} onClick={() => setSelectedMember(row)}
          className="text-xs px-2 py-0.5 rounded border border-gray-600 hover:bg-gray-700">Details</button>
      ),
    },
  ];

  const auditCols: ColumnDef<AuditEvent>[] = [
    { key: "action", header: "Action", sortable: true },
    { key: "actor", header: "Actor", width: "w-36" },
    { key: "resource_type", header: "Resource", width: "w-32" },
    { key: "created_at", header: "When", width: "w-36" },
    { key: "_actions", header: "", width: "w-16",
      render: (_: AuditEvent, i: number) => <span data-testid={`audit-row-${i}`} className="text-xs text-gray-500">#{i}</span>,
    },
  ];

  return (
    <PageShell title="Admin Console" subtitle="Tenant management, RBAC v2, and audit">
      <div data-testid="admin-page" className="space-y-4">
        <div className="flex gap-2 border-b border-gray-700 pb-1">
          <button onClick={() => setTab("tenants")} className={`px-3 py-1.5 text-sm font-medium rounded-t ${tab==="tenants"?"bg-gray-800 text-blue-300 border border-b-0 border-gray-700":"text-gray-400 hover:text-gray-200"}`}>
            Tenants &amp; Members
          </button>
          <button data-testid="admin-audit-tab" onClick={() => setTab("audit")} className={`px-3 py-1.5 text-sm font-medium rounded-t ${tab==="audit"?"bg-gray-800 text-blue-300 border border-b-0 border-gray-700":"text-gray-400 hover:text-gray-200"}`}>
            Audit Log
          </button>
        </div>

        {tab === "tenants" && (
          <div className="grid grid-cols-5 gap-4">
            <div className="col-span-2 space-y-2">
              <h3 className="text-xs font-semibold uppercase tracking-widest text-gray-500">Tenants</h3>
              {!loading && <DataTable<Tenant> data-testid="tenants-table-ready" columns={tenantCols} data={tenants} rowKey="tenant_id" emptyLabel="No tenants" />}
            </div>
            <div className="col-span-3 space-y-2">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold uppercase tracking-widest text-gray-500">Members — {selectedTenant?.name ?? "select a tenant"}</h3>
                <div className="flex items-center gap-2">
                  <input type="email" placeholder="user@example.com" value={inviteEmail} onChange={e => setInviteEmail(e.target.value)}
                    className="rounded bg-gray-800 border border-gray-600 px-2 py-1 text-xs text-gray-100 placeholder-gray-500 focus:outline-none w-44" />
                  <select value={inviteRole} onChange={e => setInviteRole(e.target.value)}
                    className="rounded bg-gray-800 border border-gray-600 px-2 py-1 text-xs text-gray-100">
                    {["VIEWER","ANALYST","ADMIN","OWNER"].map(r => <option key={r} value={r}>{r}</option>)}
                  </select>
                  <button data-testid="invite-btn" disabled={inviting || !inviteEmail} onClick={handleInvite}
                    className="rounded bg-blue-600 px-3 py-1 text-xs font-semibold text-white hover:bg-blue-500 disabled:opacity-40">
                    {inviting ? "…" : "Invite"}
                  </button>
                </div>
              </div>
              <DataTable<Member> data-testid="members-table-ready" columns={memberCols} data={members} rowKey="membership_id" emptyLabel="No members" />
            </div>
          </div>
        )}

        {tab === "audit" && (
          <DataTable<AuditEvent> data-testid="audit-list-ready" columns={auditCols} data={auditEvents} emptyLabel="No audit events" />
        )}
      </div>

      <RightDrawer open={!!selectedMember} onClose={() => setSelectedMember(null)} title={selectedMember?.display_name ?? "Member Detail"}>
        {selectedMember && (
          <div className="space-y-3 text-sm">
            <p><span className="text-gray-400">Email:</span> {selectedMember.email}</p>
            <p><span className="text-gray-400">Role:</span> <span className="font-semibold text-blue-300">{selectedMember.role}</span></p>
            <p><span className="text-gray-400">Joined:</span> {selectedMember.joined_at}</p>
            <div>
              <p className="text-gray-400 mb-1 text-xs">Permissions:</p>
              <div className="flex flex-wrap gap-1">
                {(ROLE_PERMS[selectedMember.role] ?? []).map(p => <PermissionBadge key={p} action={p} granted role={selectedMember.role} />)}
              </div>
            </div>
          </div>
        )}
      </RightDrawer>
    </PageShell>
  );
}
