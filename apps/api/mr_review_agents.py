"""
RiskCanvas v4.50.0-v4.53.0 — Agentic MR Review Workflows (Wave 26)

Provides:
- PlannerAgent: deterministic review plan (checklist + tool budget)
- ScannerAgent: secret scan, TODO/FIXME, risky patterns, policy hints
- RecommenderAgent: structured recommendations with severity + file/line
- Trace model: steps[], tool_calls[], inputs_hash, outputs_hash, audit_chain
- Export: mr-review-pack (trace.json + findings.json + recommendations.json)
No external calls. Safe for DEMO, tests, CI.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
VERSION = "v4.53.0"
ASOF = "2026-02-19T09:00:00Z"

# ─────────────────── Helpers ─────────────────────────────────────────────────

def _sha(data: Any) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=True).encode()).hexdigest()

def _compact(data: Any) -> str:
    return _sha(data)[:16]

def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"

def _chain_head() -> str:
    return "mrreview_chain_a1b2c3d4"

# ─────────────────── MR Fixtures ─────────────────────────────────────────────

_MR_FIXTURES: Dict[str, Dict[str, Any]] = {
    "MR-101": {
        "iid": 101, "title": "Refactor Black-Scholes pricing module",
        "author": "alice", "state": "opened", "target_branch": "main",
        "diff": """--- a/apps/api/hedge_engine.py
+++ b/apps/api/hedge_engine.py
@@ -10,6 +10,8 @@
 import math
+# TODO: add volatility surface interpolation
+AWS_SECRET_KEY = 'AKIAIOSFODNN7EXAMPLE'
 def price_option(S, K, r, sigma, T):
-    d1 = (math.log(S/K) + (r + sigma**2 / 2) * T) / (sigma * math.sqrt(T))
+    d1 = (math.log(S/K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
     d2 = d1 - sigma * math.sqrt(T)
""",
    },
    "MR-102": {
        "iid": 102, "title": "Add credit spread shock scenarios",
        "author": "bob", "state": "opened", "target_branch": "main",
        "diff": """--- a/apps/api/credit.py
+++ b/apps/api/credit.py
@@ -5,4 +5,10 @@
+def apply_parallel_shock(spreads, bps):
+    # FIXME: verify this handles negative spreads correctly
+    return {k: v + bps/10000.0 for k, v in spreads.items()}
+
+def risky_eval(code_str):
+    return eval(code_str)  # DANGEROUS: remove before merge
""",
    },
    "MR-103": {
        "iid": 103, "title": "CI pipeline hardening",
        "author": "charlie", "state": "opened", "target_branch": "main",
        "diff": """--- a/.gitlab-ci.yml
+++ b/.gitlab-ci.yml
@@ -1,5 +1,9 @@
+stages: [build, test, security, deploy]
 build:
   script:
-    - npm run build
+    - npm ci --prefer-offline
+    - npm run build
+security:
+  script: ['trivy fs .']
""",
    },
    "MR-104": {
        "iid": 104, "title": "Update FX exposure calculation",
        "author": "diana", "state": "opened", "target_branch": "main",
        "diff": """--- a/apps/api/fx.py
+++ b/apps/api/fx.py
@@ -20,3 +20,7 @@
+def compute_exposure_v2(portfolio, base_ccy='USD'):
+    total = sum(abs(pos['notional_usd']) for pos in portfolio)
+    return {'total_exposure': total, 'base_ccy': base_ccy}
""",
    },
}

# ─────────────────── Scan Patterns ───────────────────────────────────────────

_SECRET_PATTERNS = [
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key", "CRITICAL"),
    (r"[A-Za-z0-9+/]{40}", "Possible base64 secret", "HIGH"),
    (r"password\s*=\s*['\"][^'\"]+['\"]", "Hardcoded password", "CRITICAL"),
    (r"api[_-]?key\s*=\s*['\"][^'\"]+['\"]", "API key", "HIGH"),
    (r"ghp_[A-Za-z0-9]{36}", "GitHub PAT", "CRITICAL"),
]

_TODO_PATTERNS = [
    (r"#\s*TODO", "TODO comment", "INFO"),
    (r"#\s*FIXME", "FIXME comment", "MEDIUM"),
    (r"#\s*HACK", "HACK comment", "MEDIUM"),
]

_RISKY_PATTERNS = [
    (r"\beval\s*\(", "eval() usage — code injection risk", "CRITICAL"),
    (r"\bexec\s*\(", "exec() usage — code injection risk", "CRITICAL"),
    (r"\bsubprocess\.call\s*\(", "subprocess.call — command injection risk", "HIGH"),
    (r"\bos\.system\s*\(", "os.system() — command injection risk", "HIGH"),
    (r"\bpickle\.load\s*\(", "pickle.load — deserialization risk", "HIGH"),
]

def _scan_diff(diff_text: str) -> List[Dict[str, Any]]:
    """Deterministic scanner: scan diff lines for secrets, TODOs, risky patterns."""
    findings: List[Dict[str, Any]] = []
    lines = diff_text.split("\n")
    for ln, line in enumerate(lines, 1):
        if not line.startswith("+"):
            continue
        stripped = line[1:]
        for pattern, label, severity in _SECRET_PATTERNS + _TODO_PATTERNS + _RISKY_PATTERNS:
            if re.search(pattern, stripped):
                fid = _compact({"pattern": pattern, "line": ln, "text": stripped})
                findings.append({
                    "finding_id": fid,
                    "type": label,
                    "severity": severity,
                    "line": ln,
                    "diff_snippet": stripped[:120],
                    "rule": pattern[:40],
                })
    # stable ordering
    findings.sort(key=lambda f: (f["severity"], f["line"]))
    return findings


# ─────────────────── Agent Logic ─────────────────────────────────────────────

def _planner_agent(mr_id: str, options: Dict[str, Any]) -> Dict[str, Any]:
    mr = _MR_FIXTURES.get(mr_id)
    if not mr:
        raise ValueError(f"MR fixture not found: {mr_id}")
    checklist = [
        "scan_secrets", "scan_todos", "scan_risky_patterns",
        "check_policy_compliance", "generate_recommendations",
    ]
    tool_budget = options.get("tool_budget", {"max_tools": 5, "max_steps": 3})
    plan_payload = {"mr_id": mr_id, "checklist": checklist, "tool_budget": tool_budget, "version": VERSION}
    plan_id = _sha(plan_payload)[:24]
    return {
        "plan_id": plan_id,
        "mr_id": mr_id,
        "mr_title": mr["title"],
        "checklist": checklist,
        "tool_budget": tool_budget,
        "status": "ready",
        "created_at": ASOF,
        "inputs_hash": _sha({"mr_id": mr_id, "diff": mr["diff"]}),
        "audit_chain_head": _chain_head(),
    }


def _scanner_agent(plan: Dict[str, Any]) -> Dict[str, Any]:
    mr = _MR_FIXTURES[plan["mr_id"]]
    findings = _scan_diff(mr["diff"])
    return {
        "scanner_run_id": _compact({"plan_id": plan["plan_id"], "scan": "v1"}),
        "findings": findings,
        "finding_count": len(findings),
        "critical_count": sum(1 for f in findings if f["severity"] == "CRITICAL"),
        "high_count": sum(1 for f in findings if f["severity"] == "HIGH"),
        "medium_count": sum(1 for f in findings if f["severity"] == "MEDIUM"),
        "outputs_hash": _sha(findings),
    }


def _recommender_agent(plan: Dict[str, Any], scanner: Dict[str, Any]) -> Dict[str, Any]:
    findings = scanner["findings"]
    recs: List[Dict[str, Any]] = []
    for f in findings:
        action = "remove" if f["severity"] == "CRITICAL" else ("fix" if f["severity"] == "HIGH" else "review")
        rec_payload = {"finding_id": f["finding_id"], "action": action}
        recs.append({
            "rec_id": _compact(rec_payload),
            "finding_id": f["finding_id"],
            "severity": f["severity"],
            "action": action,
            "message": f"[{f['severity']}] {f['type']}: {action} before merge — line {f['line']}",
            "file_hint": "diff",
            "line": f["line"],
        })
    # Add general recommendation if no critical findings
    if scanner["critical_count"] == 0 and len(recs) == 0:
        recs.append({
            "rec_id": _compact({"plan_id": plan["plan_id"], "type": "general"}),
            "finding_id": None, "severity": "INFO", "action": "approve",
            "message": "No critical issues found. MR can be approved.",
            "file_hint": "diff", "line": 0,
        })
    verdict = "BLOCK" if scanner["critical_count"] > 0 else ("REVIEW" if scanner["high_count"] > 0 else "APPROVE")
    return {
        "recommendations": recs,
        "verdict": verdict,
        "rec_count": len(recs),
        "outputs_hash": _sha(recs),
    }


def _build_trace(plan: Dict[str, Any], scanner: Dict[str, Any], recommender: Dict[str, Any]) -> Dict[str, Any]:
    steps = [
        {"step": 1, "name": "plan", "status": "done", "tool": "PlannerAgent", "outputs_hash": _sha(plan)},
        {"step": 2, "name": "scan", "status": "done", "tool": "ScannerAgent", "outputs_hash": scanner["outputs_hash"]},
        {"step": 3, "name": "recommend", "status": "done", "tool": "RecommenderAgent", "outputs_hash": recommender["outputs_hash"]},
    ]
    return {
        "steps": steps,
        "tool_calls": ["PlannerAgent", "ScannerAgent", "RecommenderAgent"],
        "inputs_hash": plan["inputs_hash"],
        "outputs_hash": _sha({"scan": scanner["outputs_hash"], "rec": recommender["outputs_hash"]}),
        "audit_chain_head_hash": _chain_head(),
    }


# ─────────────────── In-memory store ─────────────────────────────────────────

_REVIEWS: Dict[str, Dict[str, Any]] = {}
_PLANS: Dict[str, Dict[str, Any]] = {}


def reset_reviews() -> None:
    _REVIEWS.clear()
    _PLANS.clear()


# ─────────────────── Public API Functions ─────────────────────────────────────

def plan_mr_review(mr_id: str, options: Dict[str, Any]) -> Dict[str, Any]:
    plan = _planner_agent(mr_id, options)
    _PLANS[plan["plan_id"]] = plan
    return plan


def run_mr_review(plan_id: str) -> Dict[str, Any]:
    plan = _PLANS.get(plan_id)
    if not plan:
        raise ValueError(f"Plan not found: {plan_id}")
    scanner = _scanner_agent(plan)
    recommender = _recommender_agent(plan, scanner)
    trace = _build_trace(plan, scanner, recommender)
    review_id = _sha({"plan_id": plan_id, "run": "v1"})[:24]
    mr = _MR_FIXTURES[plan["mr_id"]]
    review = {
        "review_id": review_id,
        "mr_id": plan["mr_id"],
        "mr_title": plan["mr_title"],
        "plan_id": plan_id,
        "verdict": recommender["verdict"],
        "findings": scanner["findings"],
        "finding_count": scanner["finding_count"],
        "critical_count": scanner["critical_count"],
        "high_count": scanner["high_count"],
        "recommendations": recommender["recommendations"],
        "rec_count": recommender["rec_count"],
        "trace": trace,
        "diff": mr["diff"],
        "created_at": ASOF,
        "output_hash": trace["outputs_hash"],
        "audit_chain_head_hash": _chain_head(),
    }
    _REVIEWS[review_id] = review
    return review


def get_mr_review(review_id: str) -> Dict[str, Any]:
    r = _REVIEWS.get(review_id)
    if not r:
        raise ValueError(f"Review not found: {review_id}")
    return r


def list_mr_fixtures() -> List[Dict[str, Any]]:
    return [{"mr_id": k, "title": v["title"], "author": v["author"], "iid": v["iid"]} for k, v in _MR_FIXTURES.items()]


def generate_comment_preview(review_id: str) -> List[Dict[str, Any]]:
    review = get_mr_review(review_id)
    comments = []
    for rec in review["recommendations"]:
        body = f"**[RiskCanvas Review Bot]** `{rec['severity']}` — {rec['message']}\n\n> Action: `{rec['action']}`"
        cid = _compact({"review_id": review_id, "rec_id": rec["rec_id"]})
        comments.append({
            "comment_id": cid,
            "review_id": review_id,
            "rec_id": rec["rec_id"],
            "severity": rec["severity"],
            "body": body,
            "line": rec["line"],
            "posted": False,
        })
    return comments


_POSTED_COMMENTS: Dict[str, List[Dict[str, Any]]] = {}


def post_comments_demo(review_id: str, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
    if review_id not in _REVIEWS:
        raise ValueError(f"Review not found: {review_id}")
    posted = [dict(c, posted=True, posted_at=ASOF) for c in comments]
    _POSTED_COMMENTS[review_id] = posted
    return {
        "review_id": review_id,
        "posted_count": len(posted),
        "comments": posted,
        "output_hash": _sha(posted),
        "demo_mode": True,
    }


def build_mr_review_pack(review_id: str) -> Dict[str, Any]:
    review = get_mr_review(review_id)
    files = [
        {"name": "trace.json", "content": json.dumps(review["trace"], indent=2)},
        {"name": "findings.json", "content": json.dumps(review["findings"], indent=2)},
        {"name": "recommendations.json", "content": json.dumps(review["recommendations"], indent=2)},
        {"name": "diff.txt", "content": review["diff"]},
    ]
    pack_payload = {"review_id": review_id, "files": [f["name"] for f in files]}
    return {
        "review_id": review_id,
        "mr_id": review["mr_id"],
        "verdict": review["verdict"],
        "files": files,
        "file_count": len(files),
        "pack_hash": _sha(pack_payload),
        "output_hash": review["output_hash"],
        "audit_chain_head_hash": _chain_head(),
        "exported_at": ASOF,
    }


# ─────────────────── Routers ────────────────────────────────────────────────

mr_review_router = APIRouter(tags=["mr_review"])
mr_review_exports_router = APIRouter(tags=["mr_review_exports"])


class PlanRequest(BaseModel):
    mr_id: str = Field(default="MR-101")
    options: Dict[str, Any] = Field(default_factory=dict)


class RunRequest(BaseModel):
    plan_id: str


class CommentPreviewRequest(BaseModel):
    review_id: str


class PostCommentsRequest(BaseModel):
    review_id: str
    comments: List[Dict[str, Any]] = Field(default_factory=list)


@mr_review_router.get("/mr/fixtures")
def api_list_fixtures():
    return {"fixtures": list_mr_fixtures()}


@mr_review_router.post("/mr/review/plan")
def api_plan_review(req: PlanRequest):
    try:
        return plan_mr_review(req.mr_id, req.options)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@mr_review_router.post("/mr/review/run")
def api_run_review(req: RunRequest):
    try:
        return run_mr_review(req.plan_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@mr_review_router.get("/mr/review/{review_id}")
def api_get_review(review_id: str):
    try:
        return get_mr_review(review_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@mr_review_router.post("/mr/review/comments/preview")
def api_comment_preview(req: CommentPreviewRequest):
    try:
        return {"comments": generate_comment_preview(req.review_id)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@mr_review_router.post("/mr/review/comments/post")
def api_post_comments(req: PostCommentsRequest):
    try:
        return post_comments_demo(req.review_id, req.comments)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@mr_review_exports_router.post("/exports/mr-review-pack")
def api_export_pack(req: CommentPreviewRequest):
    try:
        return build_mr_review_pack(req.review_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
