const PERM_LABELS: Record<string, { label: string; color: string }> = {
  "tenant.read":       { label: "Tenant Read",       color: "lime" },
  "tenant.write":      { label: "Tenant Write",      color: "green" },
  "audit.read":        { label: "Audit Read",         color: "cyan" },
  "policy.write":      { label: "Policy Write",       color: "violet" },
  "exports.write":     { label: "Exports Write",      color: "blue" },
  "jobs.write":        { label: "Jobs Write",          color: "indigo" },
  "admin.read":        { label: "Admin Read",         color: "orange" },
  "admin.write":       { label: "Admin Write",        color: "red" },
  "artifacts.read":    { label: "Artifacts Read",     color: "teal" },
  "artifacts.write":   { label: "Artifacts Write",    color: "emerald" },
  "attestations.read": { label: "Attestations Read",  color: "sky" },
  "compliance.write":  { label: "Compliance Write",   color: "purple" },
};

const COLOR_MAP: Record<string, string> = {
  lime:    "bg-lime-900/40 text-lime-300 border-lime-700",
  green:   "bg-green-900/40 text-green-300 border-green-700",
  cyan:    "bg-cyan-900/40 text-cyan-300 border-cyan-700",
  violet:  "bg-violet-900/40 text-violet-300 border-violet-700",
  blue:    "bg-blue-900/40 text-blue-300 border-blue-700",
  indigo:  "bg-indigo-900/40 text-indigo-300 border-indigo-700",
  orange:  "bg-orange-900/40 text-orange-300 border-orange-700",
  red:     "bg-red-900/40 text-red-300 border-red-700",
  teal:    "bg-teal-900/40 text-teal-300 border-teal-700",
  emerald: "bg-emerald-900/40 text-emerald-300 border-emerald-700",
  sky:     "bg-sky-900/40 text-sky-300 border-sky-700",
  purple:  "bg-purple-900/40 text-purple-300 border-purple-700",
  gray:    "bg-gray-800 text-gray-400 border-gray-600",
};

interface PermissionBadgeProps {
  action: string;
  granted?: boolean;
  role?: string;
  onClick?: () => void;
}

export default function PermissionBadge({
  action,
  granted = true,
  role,
  onClick,
}: PermissionBadgeProps) {
  const meta = PERM_LABELS[action];
  const label = meta?.label ?? action;
  const colorKey = granted ? (meta?.color ?? "gray") : "gray";
  const cls = COLOR_MAP[colorKey] ?? COLOR_MAP.gray;

  return (
    <span
      data-testid={`perm-badge-${action}`}
      title={
        granted
          ? `${label} — granted (${role ?? "?"})`
          : `${label} — denied (requires higher role)`
      }
      onClick={onClick}
      className={`inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-[10px] font-medium
        ${cls} ${granted ? "" : "opacity-40 cursor-pointer"}`}
    >
      {!granted && (
        <svg className="h-3 w-3 shrink-0" viewBox="0 0 20 20" fill="currentColor">
          <path
            fillRule="evenodd"
            d="M10 1a4.5 4.5 0 0 0-4.5 4.5V9H5a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-6a2 2 0 0 0-2-2h-.5V5.5A4.5 4.5 0 0 0 10 1zm3 8V5.5a3 3 0 1 0-6 0V9h6z"
          />
        </svg>
      )}
      {label}
    </span>
  );
}

interface PermExplainDrawerProps {
  open: boolean;
  onClose: () => void;
  action: string;
  currentRole: string;
  requiredRole: string;
}

export function PermExplainDrawer({
  open,
  onClose,
  action,
  currentRole,
  requiredRole,
}: PermExplainDrawerProps) {
  if (!open) return null;
  const meta = PERM_LABELS[action];
  const label = meta?.label ?? action;

  return (
    <div
      data-testid="perm-explain-drawer"
      className="fixed inset-y-0 right-0 z-50 flex w-80 flex-col bg-gray-900 shadow-xl border-l border-gray-700"
    >
      <div className="flex items-center justify-between border-b border-gray-700 px-4 py-3">
        <span className="text-sm font-semibold text-gray-100">
          Permission Required
        </span>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-200"
          aria-label="Close"
        >
          ✕
        </button>
      </div>
      <div className="flex-1 space-y-4 overflow-y-auto p-4 text-sm text-gray-300">
        <div>
          <span className="text-xs uppercase tracking-widest text-gray-500">
            Permission
          </span>
          <p className="mt-1 font-medium text-gray-100">{label}</p>
          <p className="text-xs text-gray-400 mt-0.5 font-mono">{action}</p>
        </div>
        <div>
          <span className="text-xs uppercase tracking-widest text-gray-500">
            Your Current Role
          </span>
          <p className="mt-1 font-medium text-yellow-300">{currentRole}</p>
        </div>
        <div>
          <span className="text-xs uppercase tracking-widest text-gray-500">
            Minimum Required Role
          </span>
          <p className="mt-1 font-medium text-red-400">{requiredRole}</p>
        </div>
        <div className="rounded bg-gray-800 p-3 text-xs text-gray-400">
          To enable this action, ask your tenant Owner or Admin to upgrade your
          role to <strong className="text-gray-200">{requiredRole}</strong> or
          higher.
        </div>
      </div>
    </div>
  );
}
