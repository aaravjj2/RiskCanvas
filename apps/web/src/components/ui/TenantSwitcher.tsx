import { useEffect, useState } from "react";

interface Tenant {
  tenant_id: string;
  name: string;
  slug: string;
  member_count: number;
}

interface TenantSwitcherProps {
  onSwitch?: (tenantId: string) => void;
}

export default function TenantSwitcher({ onSwitch }: TenantSwitcherProps) {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [currentId, setCurrentId] = useState<string>("");
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/tenants", { headers: { "x-demo-role": "OWNER" } })
      .then((r) => r.json())
      .then((d) => {
        setTenants(d.tenants ?? []);
        setCurrentId(d.current_tenant_id ?? "");
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const current = tenants.find((t) => t.tenant_id === currentId);

  function select(id: string) {
    setCurrentId(id);
    setOpen(false);
    onSwitch?.(id);
  }

  if (loading) {
    return (
      <span
        data-testid="tenant-switcher"
        className="text-xs text-gray-400 px-2 py-1"
      >
        Loading…
      </span>
    );
  }

  return (
    <div className="relative flex-shrink-0" data-testid="tenant-switcher">
      <button
        data-testid="tenant-current"
        onClick={() => setOpen((o) => !o)}
        className="inline-flex items-center gap-1 rounded border border-gray-600 bg-gray-800 px-2 py-1 text-xs font-medium text-gray-200 hover:bg-gray-700 focus:outline-none"
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <span className="max-w-[140px] truncate">
          {current?.name ?? "Select tenant"}
        </span>
        <svg className="h-3 w-3 shrink-0" viewBox="0 0 20 20" fill="currentColor">
          <path
            fillRule="evenodd"
            d="M5.23 7.21a.75.75 0 0 1 1.06.02L10 11.17l3.71-3.94a.75.75 0 1 1 1.08 1.04l-4.25 4.5a.75.75 0 0 1-1.08 0l-4.25-4.5a.75.75 0 0 1 .02-1.06z"
          />
        </svg>
      </button>

      {open && (
        <ul
          role="listbox"
          className="absolute left-0 top-8 z-50 min-w-[200px] rounded border border-gray-600 bg-gray-900 shadow-lg"
        >
          {tenants.map((t) => (
            <li
              key={t.tenant_id}
              role="option"
              aria-selected={t.tenant_id === currentId}
              data-testid={`tenant-option-${t.tenant_id}`}
              onClick={() => select(t.tenant_id)}
              className={`cursor-pointer px-3 py-2 text-xs hover:bg-gray-700 ${
                t.tenant_id === currentId
                  ? "bg-blue-900/40 text-blue-300"
                  : "text-gray-200"
              }`}
            >
              <div className="font-medium">{t.name}</div>
              <div className="text-gray-400">{t.member_count} member(s)</div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
