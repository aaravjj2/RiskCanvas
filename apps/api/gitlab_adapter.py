"""
RiskCanvas v4.42.0–v4.44.0 — GitLab Adapter (Offline Fixtures) (Wave 23)

Provides:
- GitLabAdapter interface (abstract)
- FixtureGitLabAdapter: deterministic, reads from /fixtures/gitlab/* (DEMO safe)
- RealGitLabAdapter: guarded — only activates when:
    GITLAB_MODE=real AND DEMO_MODE=false AND GITLAB_TOKEN present
  Tests MUST assert it never activates in DEMO.
- Endpoints: GET /gitlab/mrs, GET /gitlab/mrs/{iid}/diff,
             POST /gitlab/mrs/{iid}/comment
- MR compliance pack export
No live network calls in DEMO mode. Safe for tests, CI.
"""
from __future__ import annotations

import hashlib
import json
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
GITLAB_MODE = os.getenv("GITLAB_MODE", "demo").lower()
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN", "")
GITLAB_VERSION = "v1.0"
ASOF = "2026-02-19T09:00:00Z"


# ─────────────────── Helpers ─────────────────────────────────────────────────


def _sha256(data: Any) -> str:
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def _chain_head() -> str:
    return "gitlab_d4e5f6a7b8"


def _is_real_mode() -> bool:
    """Hard guard: real mode only if explicitly configured AND not in DEMO."""
    return (
        GITLAB_MODE == "real"
        and not DEMO_MODE
        and bool(GITLAB_TOKEN)
    )


# ─────────────────── Abstract Interface ─────────────────────────────────────


class GitLabAdapter(ABC):
    @abstractmethod
    def list_merge_requests(self) -> List[Dict[str, Any]]: ...

    @abstractmethod
    def get_mr_diff(self, iid: int) -> Dict[str, Any]: ...

    @abstractmethod
    def post_comment(self, iid: int, body: str) -> Dict[str, Any]: ...

    @abstractmethod
    def upload_artifact(self, iid: int, filename: str, content: str) -> Dict[str, Any]: ...


# ─────────────────── Fixture Data ────────────────────────────────────────────

_FIXTURE_MRS: List[Dict[str, Any]] = [
    {
        "iid": 101,
        "title": "feat: add FX exposure calculator to portfolio engine",
        "state": "opened",
        "author": "alice",
        "target_branch": "main",
        "source_branch": "feat/fx-exposure",
        "created_at": "2026-02-10T10:00:00Z",
        "updated_at": "2026-02-18T14:30:00Z",
        "labels": ["enhancement", "risk-engine"],
        "additions": 187,
        "deletions": 12,
        "has_conflicts": False,
    },
    {
        "iid": 102,
        "title": "fix: correct spread DV01 interpolation at boundary tenors",
        "state": "opened",
        "author": "bob",
        "target_branch": "main",
        "source_branch": "fix/dv01-boundary",
        "created_at": "2026-02-14T08:00:00Z",
        "updated_at": "2026-02-18T16:00:00Z",
        "labels": ["bug", "credit"],
        "additions": 34,
        "deletions": 28,
        "has_conflicts": False,
    },
    {
        "iid": 103,
        "title": "chore: update CI template for Wave 23 compliance checks",
        "state": "merged",
        "author": "carol",
        "target_branch": "main",
        "source_branch": "chore/ci-wave23",
        "created_at": "2026-02-12T12:00:00Z",
        "updated_at": "2026-02-15T09:20:00Z",
        "labels": ["ci", "compliance"],
        "additions": 56,
        "deletions": 18,
        "has_conflicts": False,
    },
    {
        "iid": 104,
        "title": "SECURITY: remove hardcoded API key from config loader",
        "state": "opened",
        "author": "devsec_bot",
        "target_branch": "main",
        "source_branch": "sec/remove-hardcoded-key",
        "created_at": "2026-02-17T07:00:00Z",
        "updated_at": "2026-02-19T06:00:00Z",
        "labels": ["security", "critical"],
        "additions": 8,
        "deletions": 3,
        "has_conflicts": False,
    },
]

_FIXTURE_DIFFS: Dict[int, Dict[str, Any]] = {
    101: {
        "iid": 101,
        "diff_stats": {"additions": 187, "deletions": 12, "total": 199},
        "files": [
            {
                "path": "apps/api/fx.py",
                "additions": 142,
                "deletions": 0,
                "diff_snippet": (
                    "+def compute_fx_exposure(portfolio, base_ccy='USD'):\n"
                    "+    \"\"\"Compute FX exposure by currency.\"\"\"\n"
                    "+    exposure_by_ccy = {}\n"
                    "+    for item in portfolio:\n"
                    "+        ccy = item.get('native_ccy', 'USD')\n"
                    "+        exposure_by_ccy[ccy] = exposure_by_ccy.get(ccy, 0) + item['notional']\n"
                    "+    return exposure_by_ccy\n"
                ),
            },
            {
                "path": "apps/api/tests/test_fx.py",
                "additions": 45,
                "deletions": 12,
                "diff_snippet": (
                    "+def test_fx_exposure_determinism():\n"
                    "+    r1 = compute_fx_exposure(DEMO_PORTFOLIO)\n"
                    "+    r2 = compute_fx_exposure(DEMO_PORTFOLIO)\n"
                    "+    assert r1['output_hash'] == r2['output_hash']\n"
                ),
            },
        ],
        "policy_flags": [],
        "hash": _sha256({"iid": 101}),
        "audit_chain_head_hash": _chain_head(),
    },
    102: {
        "iid": 102,
        "diff_stats": {"additions": 34, "deletions": 28, "total": 62},
        "files": [
            {
                "path": "apps/api/credit.py",
                "additions": 34,
                "deletions": 28,
                "diff_snippet": (
                    "-    if tenor <= min(nodes):\n"
                    "-        return nodes[min(nodes)]\n"
                    "+    tenors = sorted(nodes.keys())\n"
                    "+    if tenor <= tenors[0]:\n"
                    "+        return nodes[tenors[0]]\n"
                    "+    if tenor >= tenors[-1]:\n"
                    "+        return nodes[tenors[-1]]\n"
                ),
            }
        ],
        "policy_flags": [],
        "hash": _sha256({"iid": 102}),
        "audit_chain_head_hash": _chain_head(),
    },
    103: {
        "iid": 103,
        "diff_stats": {"additions": 56, "deletions": 18, "total": 74},
        "files": [
            {
                "path": ".gitlab-ci.yml",
                "additions": 56,
                "deletions": 18,
                "diff_snippet": (
                    "+wave23-compliance:\n"
                    "+  stage: verify\n"
                    "+  script:\n"
                    "+    - python scripts/run_compliance_check.py\n"
                    "+  rules:\n"
                    "+    - if: '$CI_MERGE_REQUEST_IID'\n"
                ),
            }
        ],
        "policy_flags": [],
        "hash": _sha256({"iid": 103}),
        "audit_chain_head_hash": _chain_head(),
    },
    104: {
        "iid": 104,
        "diff_stats": {"additions": 8, "deletions": 3, "total": 11},
        "files": [
            {
                "path": "apps/api/config.py",
                "additions": 8,
                "deletions": 3,
                "diff_snippet": (
                    "-API_KEY = 'sk-hardcoded-demo-key-1234'\n"
                    "+API_KEY = os.getenv('API_KEY', '')\n"
                    "+if not API_KEY:\n"
                    "+    import warnings\n"
                    "+    warnings.warn('API_KEY not set in environment')\n"
                ),
            }
        ],
        "policy_flags": [
            {"severity": "CRITICAL", "rule": "SEC-001", "description": "Hardcoded secret removed correctly"}
        ],
        "hash": _sha256({"iid": 104}),
        "audit_chain_head_hash": _chain_head(),
    },
}

_LOCAL_COMMENTS: List[Dict[str, Any]] = []


# ─────────────────── FixtureGitLabAdapter ─────────────────────────────────────


class FixtureGitLabAdapter(GitLabAdapter):
    """DEMO-safe deterministic adapter. Reads fixture data only. No network calls."""

    def list_merge_requests(self) -> List[Dict[str, Any]]:
        return list(_FIXTURE_MRS)

    def get_mr_diff(self, iid: int) -> Dict[str, Any]:
        if iid not in _FIXTURE_DIFFS:
            raise ValueError(f"No fixture diff for MR !{iid}")
        return dict(_FIXTURE_DIFFS[iid])

    def post_comment(self, iid: int, body: str) -> Dict[str, Any]:
        comment = {
            "iid": iid,
            "body": body,
            "author": "riskcanvas_bot",
            "created_at": ASOF,
            "id": len(_LOCAL_COMMENTS) + 1,
            "stored_locally": True,
        }
        _LOCAL_COMMENTS.append(comment)
        return comment

    def upload_artifact(self, iid: int, filename: str, content: str) -> Dict[str, Any]:
        return {
            "iid": iid,
            "filename": filename,
            "size": len(content),
            "stored_locally": True,
            "hash": _sha256({"filename": filename, "content": content}),
        }


# ─────────────────── RealGitLabAdapter (guarded) ─────────────────────────────


class RealGitLabAdapter(GitLabAdapter):
    """
    Real GitLab adapter. ONLY activates when:
    - GITLAB_MODE=real
    - DEMO_MODE=false
    - GITLAB_TOKEN is set
    If guard fails, all methods raise RuntimeError.
    """

    def _guard(self) -> None:
        if not _is_real_mode():
            raise RuntimeError(
                "RealGitLabAdapter called outside of real mode. "
                "Set GITLAB_MODE=real, DEMO_MODE=false, and GITLAB_TOKEN."
            )

    def list_merge_requests(self) -> List[Dict[str, Any]]:
        self._guard()
        raise NotImplementedError("Live GitLab calls not implemented in this delivery")

    def get_mr_diff(self, iid: int) -> Dict[str, Any]:
        self._guard()
        raise NotImplementedError("Live GitLab calls not implemented in this delivery")

    def post_comment(self, iid: int, body: str) -> Dict[str, Any]:
        self._guard()
        raise NotImplementedError("Live GitLab calls not implemented in this delivery")

    def upload_artifact(self, iid: int, filename: str, content: str) -> Dict[str, Any]:
        self._guard()
        raise NotImplementedError("Live GitLab calls not implemented in this delivery")


# ─────────────────── Factory ──────────────────────────────────────────────────


def get_gitlab_adapter() -> GitLabAdapter:
    """Return the appropriate adapter based on environment configuration."""
    if _is_real_mode():
        return RealGitLabAdapter()
    return FixtureGitLabAdapter()


# ─────────────────── Compliance Pack Builder ─────────────────────────────────


def build_mr_compliance_pack(iid: int) -> Dict[str, Any]:
    adapter = get_gitlab_adapter()
    mrs = adapter.list_merge_requests()
    mr = next((m for m in mrs if m["iid"] == iid), None)
    if not mr:
        raise ValueError(f"MR !{iid} not found")
    diff = adapter.get_mr_diff(iid)
    pack = {
        "pack_type": "mr-compliance-pack",
        "version": GITLAB_VERSION,
        "mr": mr,
        "diff": diff,
        "policy_flags": diff.get("policy_flags", []),
        "comments_stored": [c for c in _LOCAL_COMMENTS if c["iid"] == iid],
        "asof": ASOF,
        "audit_chain_head_hash": _chain_head(),
    }
    pack["pack_hash"] = _sha256(pack)
    return pack


# ─────────────────── Pydantic Models ─────────────────────────────────────────


class CommentRequest(BaseModel):
    body: str


# ─────────────────── FastAPI Routers ──────────────────────────────────────────

gitlab_router = APIRouter(prefix="/gitlab", tags=["gitlab"])


@gitlab_router.get("/mrs")
def api_list_mrs():
    adapter = get_gitlab_adapter()
    mrs = adapter.list_merge_requests()
    return {
        "merge_requests": mrs,
        "total": len(mrs),
        "mode": "fixture" if not _is_real_mode() else "real",
        "asof": ASOF,
        "audit_chain_head_hash": _chain_head(),
    }


@gitlab_router.get("/mrs/{iid}/diff")
def api_mr_diff(iid: int):
    adapter = get_gitlab_adapter()
    try:
        return adapter.get_mr_diff(iid)
    except ValueError as e:
        raise HTTPException(404, str(e))


@gitlab_router.post("/mrs/{iid}/comment")
def api_mr_comment(iid: int, req: CommentRequest):
    adapter = get_gitlab_adapter()
    return adapter.post_comment(iid, req.body)


gitlab_exports_router = APIRouter(prefix="/exports", tags=["gitlab-exports"])


@gitlab_exports_router.get("/mr-compliance-pack/{iid}")
def api_mr_compliance_pack(iid: int):
    try:
        return build_mr_compliance_pack(iid)
    except ValueError as e:
        raise HTTPException(404, str(e))
