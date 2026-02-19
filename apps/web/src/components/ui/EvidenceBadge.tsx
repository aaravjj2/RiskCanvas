import { useState } from "react";

interface EvidenceBadgeProps {
  hash: string;
  verified?: boolean;
  artifactId?: string;
  label?: string;
}

export default function EvidenceBadge({
  hash,
  verified = true,
  artifactId: _artifactId,
  label = "Evidence",
}: EvidenceBadgeProps) {
  const [copied, setCopied] = useState(false);

  function copy() {
    navigator.clipboard.writeText(hash).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  }

  const short = hash.slice(0, 8) + "…" + hash.slice(-4);

  return (
    <span
      data-testid="evidence-badge"
      title={`${label}: ${hash}`}
      className={`inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-[10px] font-mono
        ${
          verified
            ? "bg-emerald-900/30 border-emerald-700 text-emerald-300"
            : "bg-red-900/30 border-red-700 text-red-400"
        }`}
    >
      {verified ? (
        <svg className="h-3 w-3 shrink-0 text-emerald-400" viewBox="0 0 20 20" fill="currentColor">
          <path
            fillRule="evenodd"
            d="M10 1a9 9 0 1 0 0 18A9 9 0 0 0 10 1zm3.857 7.186a.75.75 0 0 0-1.214-.872l-3.483 4.79-1.88-1.88a.75.75 0 1 0-1.06 1.061l2.5 2.5a.75.75 0 0 0 1.137-.089l4-5.5z"
          />
        </svg>
      ) : (
        <svg className="h-3 w-3 shrink-0 text-red-400" viewBox="0 0 20 20" fill="currentColor">
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 1 0 0-16 8 8 0 0 0 0 16zm3.857-9.809a.75.75 0 0 0-1.214-.872l-3.483 4.79-1.88-1.88a.75.75 0 1 0-1.06 1.061l2.5 2.5a.75.75 0 0 0 1.137-.089l4-5.5z"
          />
        </svg>
      )}
      <span data-testid="evidence-hash">{short}</span>
      <span
        data-testid="evidence-verified"
        className={verified ? "text-emerald-400" : "text-red-400"}
      >
        {verified ? "✓" : "✗"}
      </span>
      <button
        onClick={copy}
        title="Copy full hash"
        className="ml-0.5 text-gray-400 hover:text-gray-200"
      >
        {copied ? "✓" : "⎘"}
      </button>
    </span>
  );
}
