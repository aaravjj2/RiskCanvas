"""
RiskCanvas v4.70.0-v4.71.0 — Search V2 (Wave 31)

Extends search with MR review, pipeline events, incident drills, workflows doc types.
Deterministic index with pre-seeded documents across all these types.
Query supports full-text match + type filter + pagination.
No external calls. Safe for DEMO, tests, CI.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
VERSION = "v4.71.0"
ASOF = "2026-02-19T11:30:00Z"


def _sha(data: Any) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def _compact(data: Any) -> str:
    return _sha(data)[:16]


# ─────────────────── Seed Documents ──────────────────────────────────────────

_SEED_DOCS = [
    # mr_review
    {"id": _compact({"t": "mr_review", "n": 1}), "type": "mr_review", "title": "MR-101 Refactor Black-Scholes pricing",
     "body": "Scanner found hardcoded AWS key and eval() in hedge_engine.py. Verdict: BLOCK. 3 findings critical.",
     "tags": ["secrets", "critical", "pricing"], "ref": "MR-101"},
    {"id": _compact({"t": "mr_review", "n": 2}), "type": "mr_review", "title": "MR-102 Credit spread shock",
     "body": "Scanner found eval() in credit.py and FIXME. Verdict: BLOCK. 2 findings critical.",
     "tags": ["eval", "critical", "credit"], "ref": "MR-102"},
    {"id": _compact({"t": "mr_review", "n": 3}), "type": "mr_review", "title": "MR-103 CI hardening",
     "body": "No secrets or risky patterns. Added Trivy security scan stage. Verdict: APPROVE.",
     "tags": ["ci", "security", "approve"], "ref": "MR-103"},
    {"id": _compact({"t": "mr_review", "n": 4}), "type": "mr_review", "title": "MR-104 FX exposure v2",
     "body": "Clean diff. No findings. New compute_exposure_v2 function. Verdict: APPROVE.",
     "tags": ["fx", "approve"], "ref": "MR-104"},
    # pipeline
    {"id": _compact({"t": "pipeline", "n": 1}), "type": "pipeline", "title": "build:main #1044 passed",
     "body": "npm ci, npm run build, trivy fs all passed in 95s. Branch: main. Triggered: push.",
     "tags": ["build", "main", "pass"], "ref": "pipeline-1044"},
    {"id": _compact({"t": "pipeline", "n": 2}), "type": "pipeline", "title": "test:main #1044 pytest 767 passed",
     "body": "All 767 pytest passed. 0 failed. Coverage 87.3%. Duration 140s.",
     "tags": ["test", "pytest", "coverage"], "ref": "pipeline-1044"},
    {"id": _compact({"t": "pipeline", "n": 3}), "type": "pipeline", "title": "security:main #1044 CRITICAL:0",
     "body": "Trivy scan: 0 critical, 2 high vulns. Snyk: all clean. Gate PASS.",
     "tags": ["security", "trivy", "pass"], "ref": "pipeline-1044"},
    # incident_drill
    {"id": _compact({"t": "drill", "n": 1}), "type": "incident_drill", "title": "API Latency Spike drill: PASS",
     "body": "Injected CPU 95%, conn pool 0. Detected p99 > 2000ms in 45s. Remediated: scale replicas, flush pool in 120s.",
     "tags": ["latency", "performance", "pass"], "ref": "api_latency_spike"},
    {"id": _compact({"t": "drill", "n": 2}), "type": "incident_drill", "title": "DB Lock Contention drill: PASS",
     "body": "Injected long txn lock. Detected db_lock_wait 5000ms. Remediated: kill blocking queries, lock timeout in 60s.",
     "tags": ["database", "lock", "critical"], "ref": "db_lock_contention"},
    {"id": _compact({"t": "drill", "n": 3}), "type": "incident_drill", "title": "Auth Token Failure drill: PASS",
     "body": "JWT key rotation without propagation. 50% auth rejection. Remediated: propagate key, bridge tokens in 45s.",
     "tags": ["auth", "security", "critical"], "ref": "auth_token_fail"},
    # workflow
    {"id": _compact({"t": "workflow", "n": 1}), "type": "workflow", "title": "release-pipeline workflow: active",
     "body": "DSL v2. 7 steps: run_tests, security_scan, build_image, deploy_staging, e2e_tests, readiness_check, deploy_production. Trigger: push to main.",
     "tags": ["release", "pipeline", "active"], "ref": "workflow-release"},
    {"id": _compact({"t": "workflow", "n": 2}), "type": "workflow", "title": "hotfix-pipeline workflow: draft",
     "body": "DSL v2. 4 steps: run_tests, build_image, readiness_check, deploy_production. Trigger: push to hotfix/*.",
     "tags": ["hotfix", "pipeline", "draft"], "ref": "workflow-hotfix"},
    # policy_v2
    {"id": _compact({"t": "policy_v2", "n": 1}), "type": "policy_v2", "title": "Risk Assessment Policy v2",
     "body": "All positions must be assessed for market, credit, and operational risk daily. Published.",
     "tags": ["risk", "compliance", "published"], "ref": "risk-assessment-policy"},
    {"id": _compact({"t": "policy_v2", "n": 2}), "type": "policy_v2", "title": "Secret Scanning Policy v1",
     "body": "All MRs must pass secret scan with 0 critical findings before merge. Draft.",
     "tags": ["security", "secrets", "draft"], "ref": "secret-scanning-policy"},
    # existing types
    {"id": _compact({"t": "risk_model", "n": 1}), "type": "risk_model", "title": "Black-Scholes pricing model",
     "body": "European option pricing via Black-Scholes. Inputs: S, K, r, sigma, T. Output: call/put price, delta, gamma.",
     "tags": ["options", "pricing", "bsm"], "ref": "black-scholes"},
    {"id": _compact({"t": "risk_model", "n": 2}), "type": "risk_model", "title": "VaR Monte Carlo model",
     "body": "Historical simulation VaR. 10000 paths. Confidence levels: 95%, 99%, 99.9%. Window: 252 days.",
     "tags": ["var", "monte-carlo", "risk"], "ref": "var-mc"},
]

_INDEX = {doc["id"]: doc for doc in _SEED_DOCS}

SUPPORTED_TYPES = sorted({d["type"] for d in _SEED_DOCS})


def _score(doc: Dict[str, Any], q: str) -> float:
    q_lower = q.lower()
    score = 0.0
    if q_lower in doc["title"].lower():
        score += 3.0
    if q_lower in doc["body"].lower():
        score += 2.0
    for tag in doc.get("tags", []):
        if q_lower in tag.lower():
            score += 1.0
    return score


# ─────────────────── Public API ───────────────────────────────────────────────

def get_index_stats() -> Dict[str, Any]:
    type_counts: Dict[str, int] = {}
    for doc in _INDEX.values():
        type_counts[doc["type"]] = type_counts.get(doc["type"], 0) + 1
    return {
        "total_docs": len(_INDEX),
        "by_type": type_counts,
        "supported_types": SUPPORTED_TYPES,
        "index_hash": _sha(list(sorted(_INDEX.keys()))),
        "version": VERSION,
        "as_of": ASOF,
    }


def query_search(q: str, doc_type: Optional[str] = None, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
    docs = list(_INDEX.values())
    if doc_type:
        docs = [d for d in docs if d["type"] == doc_type]

    if q.strip():
        scored = [(doc, _score(doc, q)) for doc in docs]
        scored = [(d, s) for d, s in scored if s > 0]
        scored.sort(key=lambda x: -x[1])
        results = [d for d, _ in scored]
    else:
        results = sorted(docs, key=lambda d: d["type"] + d["title"])

    total = len(results)
    start = (page - 1) * page_size
    end = start + page_size
    page_results = results[start:end]

    return {
        "query": q,
        "type_filter": doc_type,
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": page_results,
        "result_count": len(page_results),
        "index_hash": _sha(list(sorted(_INDEX.keys()))),
    }


# ─────────────────── Router ──────────────────────────────────────────────────

search_v2_router = APIRouter(tags=["search_v2"])


class SearchRequest(BaseModel):
    q: str = Field(default="")
    type: Optional[str] = Field(default=None)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)


@search_v2_router.get("/search/v2/stats")
def api_stats():
    return get_index_stats()


@search_v2_router.post("/search/v2/query")
def api_query(req: SearchRequest):
    return query_search(req.q, req.type, req.page, req.page_size)
