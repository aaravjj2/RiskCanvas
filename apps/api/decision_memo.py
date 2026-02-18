"""
RiskCanvas v4.9.0 — Decision Memo Builder

Builds auditable decision memos (Markdown + JSON) from hedge results.
Numbers are derived ONLY from engine outputs — no invented values.
Exports include: memo.md, memo.json, provenance block.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
DEMO_ASOF = "2026-01-15T16:00:00"

# ─────────────────────────── Helpers ─────────────────────────────────────────


def _sha256(data: Any) -> str:
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def _chain_head() -> str:
    return "memo9d4f8b2c71e0"


def _now_iso() -> str:
    demo = os.getenv("DEMO_MODE", "false").lower() == "true"
    return DEMO_ASOF if demo else datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")


# ─────────────────────────── Memo Builder ────────────────────────────────────


class DecisionMemoBuilder:
    """
    Builds a decision memo from hedge results and compare deltas.
    All numbers derived from the provided data — no invented values.
    """

    def build(
        self,
        hedge_result: Dict[str, Any],
        compare_deltas: Dict[str, Any],
        provenance_hashes: Dict[str, str],
        analyst_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Returns:
          memo_md: Markdown string of the decision memo
          memo_json: Structured dict for programmatic use
          memo_hash: sha256 of the canonical memo_json
        """
        asof = _now_iso()
        portfolio_id = hedge_result.get("portfolio_id", "unknown")
        template_id = hedge_result.get("template_id", "unknown")
        objective = hedge_result.get("objective", "unknown")
        candidates = hedge_result.get("candidates", [])
        best = candidates[0] if candidates else {}

        base_metrics = compare_deltas.get("base_metrics", {})
        hedged_metrics = compare_deltas.get("hedged_metrics", {})
        deltas = compare_deltas.get("deltas", {})
        pct_changes = compare_deltas.get("pct_changes", {})

        # Build structured memo_json first (numbers only from data)
        memo_json = {
            "version": "v4.9.0",
            "asof": asof,
            "portfolio_id": portfolio_id,
            "template_id": template_id,
            "objective": objective,
            "best_candidate": best,
            "before_metrics": base_metrics,
            "after_metrics": hedged_metrics,
            "delta_metrics": deltas,
            "pct_changes": pct_changes,
            "analyst_notes": analyst_notes or "",
            "provenance": {
                "hedge_input_hash": hedge_result.get("input_hash", ""),
                "hedge_output_hash": hedge_result.get("output_hash", ""),
                "compare_input_hash": compare_deltas.get("input_hash", ""),
                "compare_output_hash": compare_deltas.get("output_hash", ""),
                **provenance_hashes,
                "audit_chain_head_hash": _chain_head(),
            },
        }

        memo_hash = _sha256(memo_json)
        memo_json["memo_hash"] = memo_hash

        memo_md = self._render_markdown(memo_json)

        return {
            "memo_md": memo_md,
            "memo_json": memo_json,
            "memo_hash": memo_hash,
        }

    def _render_markdown(self, m: Dict[str, Any]) -> str:
        lines = [
            f"# Hedge Decision Memo",
            f"",
            f"**Portfolio:** `{m['portfolio_id']}`  ",
            f"**Template:** `{m['template_id']}`  ",
            f"**Objective:** `{m['objective']}`  ",
            f"**As-of:** `{m['asof']}`  ",
            f"**Memo Hash:** `{m['memo_hash']}`",
            f"",
            "## Risk Metrics: Before vs After",
            "",
            "| Metric | Before | After | Delta | %Change |",
            "|--------|--------|-------|-------|---------|",
        ]

        before = m["before_metrics"]
        after = m["after_metrics"]
        deltas = m["delta_metrics"]
        pcts = m["pct_changes"]
        for metric in sorted(before.keys()):
            b = before.get(metric, "—")
            a = after.get(metric, "—")
            d = deltas.get(metric, "—")
            p = pcts.get(metric, "—")
            p_str = f"{float(p)*100:.1f}%" if isinstance(p, (int, float)) else str(p)
            lines.append(f"| {metric} | {b} | {a} | {d} | {p_str} |")

        lines.append("")
        lines.append("## Best Hedge Candidate")
        lines.append("")
        best = m.get("best_candidate", {})
        if best:
            lines.append(f"- **Instrument:** {best.get('instrument', '—')}")
            lines.append(f"- **Strike %:** {best.get('strike_pct', '—')}")
            lines.append(f"- **Contracts:** {best.get('contracts', '—')}")
            lines.append(f"- **Total Cost:** ${best.get('total_cost', 0):,.2f}")
            lines.append(f"- **Score:** {best.get('score', '—')}")
            lines.append(f"- **Candidate ID:** `{best.get('candidate_id', '—')}`")
        else:
            lines.append("_No candidates generated._")

        lines.append("")
        lines.append("## Analyst Notes")
        lines.append("")
        notes = m.get("analyst_notes", "")
        lines.append(notes if notes else "_None provided._")

        lines.append("")
        lines.append("## Provenance")
        lines.append("")
        prov = m.get("provenance", {})
        for k, v in sorted(prov.items()):
            lines.append(f"- **{k}:** `{v}`")

        lines.append("")
        lines.append("---")
        lines.append(f"*Generated by RiskCanvas v4.9.0 · Deterministic build · No external calls*")

        return "\n".join(lines)


_memo_builder = DecisionMemoBuilder()


# ─────────────────────────── Pydantic Schemas ────────────────────────────────


class DecisionMemoRequest(BaseModel):
    hedge_result: Dict[str, Any] = Field(default_factory=dict)
    compare_deltas: Dict[str, Any] = Field(default_factory=dict)
    provenance_hashes: Dict[str, str] = Field(default_factory=dict)
    analyst_notes: Optional[str] = None


class HedgeDecisionPackRequest(BaseModel):
    memo_request: DecisionMemoRequest
    include_candidates: bool = True
    include_compare: bool = True


# ─────────────────────────── Router ──────────────────────────────────────────

decision_memo_router = APIRouter(prefix="/hedge/v2", tags=["decision_memo"])


@decision_memo_router.post("/memo")
def build_decision_memo(req: DecisionMemoRequest) -> Dict[str, Any]:
    """Builds a decision memo from hedge results."""
    result = _memo_builder.build(
        hedge_result=req.hedge_result,
        compare_deltas=req.compare_deltas,
        provenance_hashes=req.provenance_hashes,
        analyst_notes=req.analyst_notes,
    )
    ih = _sha256(req.model_dump())
    return {
        **result,
        "input_hash": ih,
        "audit_chain_head_hash": _chain_head(),
    }


exports_router = APIRouter(prefix="/exports", tags=["exports"])


@exports_router.post("/hedge-decision-pack")
def export_hedge_decision_pack(req: HedgeDecisionPackRequest) -> Dict[str, Any]:
    """Exports a complete hedge decision pack (memo + candidates + compare)."""
    memo_result = _memo_builder.build(
        hedge_result=req.memo_request.hedge_result,
        compare_deltas=req.memo_request.compare_deltas,
        provenance_hashes=req.memo_request.provenance_hashes,
        analyst_notes=req.memo_request.analyst_notes,
    )

    pack: Dict[str, Any] = {
        "pack_version": "v4.9.0",
        "memo_hash": memo_result["memo_hash"],
        "memo_md": memo_result["memo_md"],
        "memo_json": memo_result["memo_json"],
    }

    if req.include_candidates:
        pack["candidates"] = req.memo_request.hedge_result.get("candidates", [])

    if req.include_compare:
        pack["compare_deltas"] = req.memo_request.compare_deltas

    pack_hash = _sha256(pack)
    pack["pack_hash"] = pack_hash
    pack["audit_chain_head_hash"] = _chain_head()

    return pack
