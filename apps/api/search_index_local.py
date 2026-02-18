"""
Search Index Local module (v4.3.0)

Deterministic local search index over runs, reports, audit events,
activity events, policies, eval results, and SRE playbooks.

All stored in memory from existing sqlite/in-memory stores.
Result ordering: (type_priority, score, event_id).
No external dependencies — pure Python.
Optional ElasticSearch adapter class (SEARCH_BACKEND=elastic) — OFF by default,
never instantiated in tests.
"""

import hashlib
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SEARCH_VERSION = "4.3.0"

TYPE_PRIORITY: Dict[str, int] = {
    "run": 1,
    "report": 2,
    "audit": 3,
    "activity": 4,
    "policy": 5,
    "eval": 6,
    "sre_playbook": 7,
}

DEMO_INDEX_DOCS: List[Dict[str, Any]] = [
    # runs
    {"id": "run-demo-001", "type": "run", "text": "portfolio analysis run demo-001 alice tech growth AAPL MSFT VaR", "url": "/history"},
    {"id": "run-demo-002", "type": "run", "text": "stress scenario run demo-002 carol interest rate shift VaR", "url": "/history"},
    # reports
    {"id": "rep-demo-001", "type": "report", "text": "report bundle demo-001 alice portfolio analysis hash manifest", "url": "/reports-hub"},
    {"id": "rep-demo-002", "type": "report", "text": "report bundle demo-002 bob risk summary bonds yield", "url": "/reports-hub"},
    # audit
    {"id": "audit-demo-001", "type": "audit", "text": "audit event run.execute alice demo-workspace policy allow", "url": "/audit"},
    {"id": "audit-demo-002", "type": "audit", "text": "audit event report.build bob demo-workspace report generated", "url": "/audit"},
    # activity
    {"id": "act-1", "type": "activity", "text": "activity portfolio analysis run started alice demo-workspace", "url": "/activity"},
    {"id": "act-2", "type": "activity", "text": "activity policy evaluated decision allow bob demo-workspace", "url": "/activity"},
    {"id": "act-3", "type": "activity", "text": "activity report bundle generated alice demo-workspace", "url": "/activity"},
    # policies
    {"id": "pol-demo-001", "type": "policy", "text": "policy evaluation DEMO mode allow tools 8 budget 20 no hallucination", "url": "/governance"},
    {"id": "pol-demo-002", "type": "policy", "text": "policy evaluation PROD mode block secret token redaction", "url": "/governance"},
    # evals
    {"id": "eval-demo-001", "type": "eval", "text": "eval suite governance policy suite pass rate 100% 5 cases scorecard", "url": "/governance"},
    {"id": "eval-demo-002", "type": "eval", "text": "eval suite rates curve suite pass rate 100% 2 cases", "url": "/governance"},
    # sre playbooks
    {"id": "sre-demo-001", "type": "sre_playbook", "text": "sre playbook P0 triage policy blocked pipeline fatals 3 steps", "url": "/sre"},
    {"id": "sre-demo-002", "type": "sre_playbook", "text": "sre playbook P1 mitigate degraded services redis kafka remediation", "url": "/sre"},
]


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

def tokenize(text: str) -> List[str]:
    """Lowercase split, strip punctuation."""
    return re.findall(r"[a-z0-9]+", text.lower())


def score_doc(tokens_query: List[str], doc_tokens: List[str]) -> float:
    """Simple overlap score: fraction of query tokens found in doc."""
    if not tokens_query:
        return 0.0
    hits = sum(1 for t in tokens_query if t in doc_tokens)
    return hits / len(tokens_query)


# ---------------------------------------------------------------------------
# Local index store
# ---------------------------------------------------------------------------

class SearchIndexLocal:
    def __init__(self) -> None:
        self._docs: List[Dict[str, Any]] = []
        self._index_hash: str = ""
        self._built = False

    def _sha(self, obj: Any) -> str:
        raw = json.dumps(obj, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode()).hexdigest()

    def build(self, docs: Optional[List[Dict[str, Any]]] = None) -> str:
        """Build index from docs (or DEMO_INDEX_DOCS if None). Returns index_hash."""
        self._docs = docs if docs is not None else list(DEMO_INDEX_DOCS)
        # Pre-compute token sets for each doc
        for doc in self._docs:
            doc["_tokens"] = set(tokenize(doc.get("text", "")))
        self._index_hash = self._sha({"docs": [d["id"] for d in self._docs]})
        self._built = True
        return self._index_hash

    def query(
        self,
        text: str,
        filters: Optional[List[str]] = None,
        limit: int = 20,
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Query index. Returns (results, query_hash).
        Results ordered by (type_priority, -score, id).
        """
        if not self._built:
            self.build()

        q_tokens = tokenize(text)
        results = []
        for doc in self._docs:
            # Apply type filter
            if filters and doc["type"] not in filters:
                continue
            score = score_doc(q_tokens, doc.get("_tokens", set()))
            if score > 0:
                results.append({
                    "id": doc["id"],
                    "type": doc["type"],
                    "text": doc["text"],
                    "url": doc.get("url", "/"),
                    "score": round(score, 4),
                })

        # Stable sort: type_priority ASC, score DESC, id ASC
        results.sort(key=lambda r: (TYPE_PRIORITY.get(r["type"], 99), -r["score"], r["id"]))
        results = results[:limit]

        query_hash = self._sha({"q": text, "filters": sorted(filters or []), "results": [r["id"] for r in results]})
        return results, query_hash

    def status(self) -> Dict[str, Any]:
        """Return index status: counts by type, index_hash."""
        counts: Dict[str, int] = {}
        for doc in self._docs:
            counts[doc["type"]] = counts.get(doc["type"], 0) + 1
        return {
            "built": self._built,
            "doc_count": len(self._docs),
            "counts_by_type": counts,
            "index_hash": self._index_hash,
            "version": SEARCH_VERSION,
        }

    def reset(self) -> None:
        self._docs = []
        self._index_hash = ""
        self._built = False


_local_index = SearchIndexLocal()


def get_local_index() -> SearchIndexLocal:
    return _local_index


# ---------------------------------------------------------------------------
# Optional Elastic adapter (OFF by default, never instantiated in tests)
# ---------------------------------------------------------------------------

class SearchIndexElastic:
    """
    Elastic adapter stub. Only instantiated when SEARCH_BACKEND=elastic.
    NOT used in any tests (zero network calls).
    """

    def __init__(self, url: str, index_name: str) -> None:
        self._url = url
        self._index_name = index_name

    def health_probe(self) -> Dict[str, Any]:
        """Non-destructive health check. Returns status without indexing."""
        return {"backend": "elastic", "url": self._url, "status": "NOT_CONNECTED"}

    def build(self, docs: Optional[List[Dict[str, Any]]] = None) -> str:
        raise NotImplementedError("Elastic adapter not implemented for DEMO mode")

    def query(self, text: str, filters: Optional[List[str]] = None, limit: int = 20):
        raise NotImplementedError("Elastic adapter not implemented for DEMO mode")


# ---------------------------------------------------------------------------
# FastAPI router
# ---------------------------------------------------------------------------

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

search_router = APIRouter(prefix="/search", tags=["search"])

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"


class SearchQueryRequest(BaseModel):
    text: str
    filters: Optional[List[str]] = None
    limit: int = 20


@search_router.post("/query")
def search_query(req: SearchQueryRequest) -> JSONResponse:
    idx = _local_index
    if not idx._built:
        idx.build()
    results, query_hash = idx.query(text=req.text, filters=req.filters, limit=req.limit)
    # Group results by type
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for r in results:
        grouped.setdefault(r["type"], []).append(r)
    return JSONResponse({
        "results": results,
        "grouped": grouped,
        "total": len(results),
        "query_hash": query_hash,
    })


@search_router.post("/reindex")
def reindex() -> JSONResponse:
    demo = os.getenv("DEMO_MODE", "false").lower() == "true"
    if not demo:
        raise HTTPException(status_code=403, detail="Reindex only available in DEMO mode")
    idx = _local_index
    idx.reset()
    index_hash = idx.build()
    return JSONResponse({"status": "ok", "index_hash": index_hash, "doc_count": len(idx._docs)})


@search_router.get("/status")
def search_status() -> JSONResponse:
    idx = _local_index
    if not idx._built:
        idx.build()
    return JSONResponse(idx.status())
