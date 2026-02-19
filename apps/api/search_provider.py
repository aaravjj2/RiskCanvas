"""
search_provider.py (v5.51.0 — Wave 63)

SearchProvider — pluggable search backend.

Interface:
  class SearchProvider(ABC):
    def index(doc_id, doc_type, content, meta) -> None
    def search(query, doc_types, limit) -> List[SearchResult]
    def delete(doc_id) -> None
    def stats() -> Dict

Backends:
  LocalSearchProvider  — pure-Python in-memory keyword/token search (default)
  ElasticSearchProvider — stub (only activated when SEARCH_BACKEND=elastic
                          AND ELASTIC_URL is set; no network calls in demo)

The active provider is selected at module load and can be read via
`get_provider()`.  Frontend can call /search/query to use it.

Endpoints:
  POST /search/index              — index a document
  POST /search/query              — query documents
  DELETE /search/{doc_id}         — delete document from index
  GET  /search/stats              — provider stats
  GET  /search/provider           — which provider is active
"""
from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

ASOF = "2026-02-19T00:00:00Z"
DEMO_MODE = os.getenv("DEMO_MODE", "1") == "1"


# ── Data types ─────────────────────────────────────────────────────────────────


class SearchResult:
    def __init__(
        self,
        doc_id: str,
        doc_type: str,
        score: float,
        snippet: str,
        meta: Dict[str, Any],
    ):
        self.doc_id = doc_id
        self.doc_type = doc_type
        self.score = score
        self.snippet = snippet
        self.meta = meta

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "doc_type": self.doc_type,
            "score": round(self.score, 4),
            "snippet": self.snippet,
            "meta": self.meta,
        }


# ── Provider interface ─────────────────────────────────────────────────────────


class SearchProvider(ABC):
    @abstractmethod
    def index(
        self,
        doc_id: str,
        doc_type: str,
        content: str,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None: ...

    @abstractmethod
    def search(
        self,
        query: str,
        doc_types: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[SearchResult]: ...

    @abstractmethod
    def delete(self, doc_id: str) -> None: ...

    @abstractmethod
    def stats(self) -> Dict[str, Any]: ...

    @property
    @abstractmethod
    def provider_name(self) -> str: ...


# ── Local (in-memory) provider ─────────────────────────────────────────────────


class LocalSearchProvider(SearchProvider):
    """
    Simple keyword-matching search provider using token overlap scoring.
    No external dependencies. Works fully offline/deterministically.
    """

    def __init__(self) -> None:
        self._docs: Dict[str, Dict[str, Any]] = {}

    @property
    def provider_name(self) -> str:
        return "local"

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"\w+", text.lower())

    def index(
        self,
        doc_id: str,
        doc_type: str,
        content: str,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        tokens = self._tokenize(content)
        self._docs[doc_id] = {
            "doc_id": doc_id,
            "doc_type": doc_type,
            "content": content,
            "tokens": tokens,
            "meta": meta or {},
        }

    def search(
        self,
        query: str,
        doc_types: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[SearchResult]:
        q_tokens = set(self._tokenize(query))
        if not q_tokens:
            return []

        results = []
        for doc in self._docs.values():
            if doc_types and doc["doc_type"] not in doc_types:
                continue
            doc_tokens = set(doc["tokens"])
            overlap = len(q_tokens & doc_tokens)
            if overlap == 0:
                continue
            score = overlap / max(len(q_tokens), 1)
            # Build snippet: first 120 chars of content
            snippet = doc["content"][:120].strip()
            results.append(
                SearchResult(
                    doc_id=doc["doc_id"],
                    doc_type=doc["doc_type"],
                    score=score,
                    snippet=snippet,
                    meta=doc["meta"],
                )
            )

        # Sort by score descending, then doc_id for determinism
        results.sort(key=lambda r: (-r.score, r.doc_id))
        return results[:limit]

    def delete(self, doc_id: str) -> None:
        self._docs.pop(doc_id, None)

    def stats(self) -> Dict[str, Any]:
        type_counts: Dict[str, int] = {}
        for doc in self._docs.values():
            t = doc["doc_type"]
            type_counts[t] = type_counts.get(t, 0) + 1
        return {
            "provider": self.provider_name,
            "total_documents": len(self._docs),
            "by_type": type_counts,
            "asof": ASOF,
        }


# ── Elasticsearch stub (env-gated) ────────────────────────────────────────────


class ElasticSearchProvider(SearchProvider):
    """
    Elasticsearch stub.  Only activated when:
      SEARCH_BACKEND=elastic AND ELASTIC_URL is non-empty.
    In all other cases (including DEMO mode), LocalSearchProvider is used.
    This class will never make network calls if activated via the module.
    """

    def __init__(self, elastic_url: str) -> None:
        self._url = elastic_url
        # Fallback local index for stub operation
        self._local = LocalSearchProvider()

    @property
    def provider_name(self) -> str:
        return f"elasticsearch({self._url})"

    def index(self, doc_id: str, doc_type: str, content: str, meta=None) -> None:
        # Stub: delegate to local in-memory index
        self._local.index(doc_id, doc_type, content, meta)

    def search(self, query: str, doc_types=None, limit: int = 20) -> List[SearchResult]:
        return self._local.search(query, doc_types, limit)

    def delete(self, doc_id: str) -> None:
        self._local.delete(doc_id)

    def stats(self) -> Dict[str, Any]:
        s = self._local.stats()
        s["provider"] = self.provider_name
        s["note"] = "stub — delegating to in-memory index"
        return s


# ── Provider selection ─────────────────────────────────────────────────────────


def _create_provider() -> SearchProvider:
    backend = os.getenv("SEARCH_BACKEND", "local")
    elastic_url = os.getenv("ELASTIC_URL", "")
    if backend == "elastic" and elastic_url and not DEMO_MODE:
        return ElasticSearchProvider(elastic_url)
    return LocalSearchProvider()


_provider: SearchProvider = _create_provider()


def get_provider() -> SearchProvider:
    return _provider


# ── Demo seed ──────────────────────────────────────────────────────────────────


def _seed() -> None:
    p = get_provider()
    p.index("pkt-001", "decision_packet",
            "Rate risk decision packet Q1 2026 USD SOFR curve shock 100bps",
            {"tenant": "tenant-001"})
    p.index("scn-demo-001", "scenario",
            "Rate shock scenario parallel shift 100bps SOFR curve",
            {"kind": "rate_shock"})
    p.index("ds-prov-001", "dataset",
            "Demo rates dataset synthetic SOFR curves 5000 rows CC0 license",
            {"license": "CC0"})
    p.index("rev-sla-001", "review",
            "Q1 2026 rate risk review approved SLA compliant alice reviewer",
            {"status": "APPROVED"})


_seed()


# ── HTTP Router ────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/search", tags=["search"])


class IndexRequest(BaseModel):
    doc_id: str
    doc_type: str
    content: str
    meta: Optional[Dict[str, Any]] = None


class QueryRequest(BaseModel):
    query: str
    doc_types: Optional[List[str]] = None
    limit: int = 20


@router.post("/index")
def http_index(req: IndexRequest):
    get_provider().index(req.doc_id, req.doc_type, req.content, req.meta)
    return {"indexed": req.doc_id, "provider": get_provider().provider_name}


@router.post("/query")
def http_query(req: QueryRequest):
    results = get_provider().search(req.query, req.doc_types, req.limit)
    return {
        "query": req.query,
        "count": len(results),
        "results": [r.to_dict() for r in results],
        "provider": get_provider().provider_name,
    }


@router.delete("/{doc_id}")
def http_delete(doc_id: str):
    get_provider().delete(doc_id)
    return {"deleted": doc_id}


@router.get("/stats")
def http_stats():
    return get_provider().stats()


@router.get("/provider")
def http_provider():
    return {"provider": get_provider().provider_name, "demo_mode": DEMO_MODE}
