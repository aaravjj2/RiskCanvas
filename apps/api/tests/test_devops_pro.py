"""
Tests for DevOps Pro: MR Review Bundle + Pipeline Analyzer + Artifact Pack (v3.9+)

Covers:
- MR diff scanning (allow clean, block secret, warn TODO)
- Pipeline log analysis (OOM, TIMEOUT, etc.)
- Artifact pack determinism + manifest hash
"""

import os
import base64
import json
import zipfile
import io
import pytest

os.environ["DEMO_MODE"] = "true"

from fastapi.testclient import TestClient
from main import app
from sqlmodel import SQLModel
from database import db

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_demo_mode(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    SQLModel.metadata.create_all(db.engine)
    yield


# ── POST /devops/mr/review-bundle ────────────────────────────────────────────

CLEAN_DIFF = """\
diff --git a/main.py b/main.py
--- a/main.py
+++ b/main.py
@@ -1,3 +1,4 @@
+def hello():
+    return 42
"""

SECRET_DIFF = """\
diff --git a/.env b/.env
--- /dev/null
+++ b/.env
+OPENAI_API_KEY=sk-1234567890abcdef1234567890abcdef1234567890
"""

TODO_DIFF = """\
diff --git a/utils.py b/utils.py
+++ b/utils.py
+# TODO: remove this hack
+x = eval("1+2")
"""


class TestMRReviewBundle:
    def _review(self, diff: str):
        return client.post("/devops/mr/review-bundle", json={"diff": diff})

    def test_clean_diff_allows(self):
        r = self._review(CLEAN_DIFF)
        assert r.status_code == 200
        assert r.json()["decision"] == "allow"

    def test_secret_diff_blocks(self):
        r = self._review(SECRET_DIFF)
        assert r.status_code == 200
        data = r.json()
        assert data["decision"] == "block"
        # findings are inside review_json
        findings = data["review_json"]["findings"]
        codes = [f["code"] for f in findings]
        assert any("KEY" in c or "SECRET" in c for c in codes)

    def test_todo_diff_warns(self):
        r = self._review(TODO_DIFF)
        assert r.status_code == 200
        data = r.json()
        findings = data["review_json"]["findings"]
        severities = [f["severity"] for f in findings]
        assert "warning" in severities

    def test_review_bundle_has_hash(self):
        r = self._review(CLEAN_DIFF)
        assert "bundle_hash" in r.json()

    def test_review_bundle_hash_deterministic(self):
        r1 = self._review(CLEAN_DIFF)
        r2 = self._review(CLEAN_DIFF)
        assert r1.json()["bundle_hash"] == r2.json()["bundle_hash"]

    def test_review_md_present(self):
        r = self._review(CLEAN_DIFF)
        data = r.json()
        assert "review_md" in data
        assert "##" in data["review_md"]  # has markdown headers

    def test_review_json_present(self):
        r = self._review(CLEAN_DIFF)
        data = r.json()
        # review_json should be a dict or parseable string
        assert "review_json" in data

    def test_eval_usage_warns(self):
        r = self._review(TODO_DIFF)
        findings = r.json()["review_json"]["findings"]
        codes = [f["code"] for f in findings]
        assert "EVAL_USAGE" in codes


# ── POST /devops/pipeline/analyze ────────────────────────────────────────────

OOM_LOG = "Error: Java heap space\nkilled\nfatal: out of memory\n"
TIMEOUT_LOG = "ERROR: step exceeded time limit of 3600s\ntimeout: job timed out\n"
IMPORT_ERROR_LOG = "ModuleNotFoundError: No module named 'numpy'\n"
CLEAN_LOG = "All steps succeeded.\nPipeline complete.\n"
ASSERTION_LOG = "AssertionError: expected 5 got 7\nFAILED test_main.py::test_foo\n"


class TestPipelineAnalyze:
    def _analyze(self, log: str):
        return client.post("/devops/pipeline/analyze", json={"log": log})

    def test_oom_detected(self):
        r = self._analyze(OOM_LOG)
        assert r.status_code == 200
        cats = r.json()["categories"]
        assert "OOM" in cats

    def test_timeout_detected(self):
        r = self._analyze(TIMEOUT_LOG)
        cats = r.json()["categories"]
        assert "TIMEOUT" in cats

    def test_import_error_detected(self):
        r = self._analyze(IMPORT_ERROR_LOG)
        cats = r.json()["categories"]
        assert "IMPORT_ERROR" in cats

    def test_clean_log_no_categories(self):
        r = self._analyze(CLEAN_LOG)
        assert r.status_code == 200
        data = r.json()
        assert data["fatal_count"] == 0
        assert data["error_count"] == 0

    def test_assertion_failed_detected(self):
        r = self._analyze(ASSERTION_LOG)
        cats = r.json()["categories"]
        assert "ASSERTION_FAILED" in cats or "TEST_FAILURE" in cats

    def test_findings_have_remediation(self):
        r = self._analyze(OOM_LOG)
        findings = r.json()["findings"]
        assert len(findings) > 0
        for f in findings:
            assert "remediation" in f
            assert f["remediation"]  # non-empty

    def test_log_hash_present(self):
        r = self._analyze(CLEAN_LOG)
        assert "log_hash" in r.json()


# ── POST /devops/artifacts/build ─────────────────────────────────────────────

class TestArtifactsBuild:
    def _build(self, files: dict):
        # API takes review_md and pipeline_json fields, not a generic 'files' dict
        # Use review_md for a report, and potentially pipeline_json for data
        payload = {}
        if "report.md" in files:
            payload["review_md"] = files["report.md"]
        elif "review.md" in files:
            payload["review_md"] = files["review.md"]
        else:
            # Use first value as review_md
            first_key = next(iter(files))
            payload["review_md"] = files[first_key]
        if "data.json" in files:
            payload["pipeline_json"] = files["data.json"]
        return client.post("/devops/artifacts/build", json=payload)

    def test_pack_returns_manifest_hash(self):
        r = self._build({"report.md": "# Report\nOK"})
        assert r.status_code == 200
        assert "manifest_hash" in r.json()

    def test_pack_deterministic(self):
        r1 = client.post("/devops/artifacts/build", json={"review_md": "# OK", "pipeline_json": '{"x": 1}'})
        r2 = client.post("/devops/artifacts/build", json={"review_md": "# OK", "pipeline_json": '{"x": 1}'})
        assert r1.json()["manifest_hash"] == r2.json()["manifest_hash"]

    def test_pack_b64_decodable(self):
        r = client.post("/devops/artifacts/build", json={"review_md": "hello world content"})
        b64 = r.json()["pack_b64"]
        raw = base64.b64decode(b64)
        zf = zipfile.ZipFile(io.BytesIO(raw))
        names = zf.namelist()
        assert "review.md" in names

    def test_manifest_json_inside_zip(self):
        r = client.post("/devops/artifacts/build", json={"review_md": "abc content"})
        b64 = r.json()["pack_b64"]
        raw = base64.b64decode(b64)
        zf = zipfile.ZipFile(io.BytesIO(raw))
        assert "manifest.json" in zf.namelist()

    def test_pack_size_bytes_accurate(self):
        r = client.post("/devops/artifacts/build", json={"review_md": "hello"})
        data = r.json()
        b64 = data["pack_b64"]
        expected = len(base64.b64decode(b64))
        assert data["pack_size_bytes"] == expected
