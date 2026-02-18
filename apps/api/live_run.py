"""
Live Run Progress module (v4.2.0)

Deterministic SSE-based run progress for DEMO mode.
Stages: VALIDATE → PRICE → VAR → REPORT → DONE
Each stage emits a progress event with pct.
"""

import asyncio
import hashlib
import json
import os
from typing import Any, AsyncGenerator, Dict, List, Optional

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

# ---------------------------------------------------------------------------
# Stage definitions (deterministic)
# ---------------------------------------------------------------------------

DEMO_STAGES: List[Dict[str, Any]] = [
    {"stage": "VALIDATE", "label": "Validating inputs", "pct": 10},
    {"stage": "PRICE", "label": "Pricing options", "pct": 35},
    {"stage": "VAR", "label": "Computing VaR", "pct": 60},
    {"stage": "REPORT", "label": "Building report", "pct": 85},
    {"stage": "DONE", "label": "Complete", "pct": 100},
]

# ---------------------------------------------------------------------------
# Status store (for GET /runs/{run_id}/status)
# ---------------------------------------------------------------------------

class RunStatusStore:
    def __init__(self) -> None:
        self._status: Dict[str, Dict[str, Any]] = {}

    def _sha(self, obj: Any) -> str:
        raw = json.dumps(obj, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode()).hexdigest()

    def set_stage(self, run_id: str, stage: str, pct: int, label: str) -> Dict[str, Any]:
        record = {
            "run_id": run_id,
            "stage": stage,
            "label": label,
            "pct": pct,
            "done": stage == "DONE",
        }
        record["status_hash"] = self._sha(record)
        self._status[run_id] = record
        return record

    def get(self, run_id: str) -> Optional[Dict[str, Any]]:
        return self._status.get(run_id)

    def reset(self) -> None:
        self._status = {}

    def seed_demo(self) -> None:
        """Pre-populate demo-run-001 in DONE state."""
        rec = self.set_stage("run-demo-001", "DONE", 100, "Complete")
        return rec


_run_status_store = RunStatusStore()


def get_run_status_store() -> RunStatusStore:
    return _run_status_store


# ---------------------------------------------------------------------------
# SSE generator for run progress
# ---------------------------------------------------------------------------

async def run_progress_generator(run_id: str) -> AsyncGenerator[str, None]:
    """
    In DEMO mode: replay deterministic stage sequence.
    Each event: data: <json>\n\n
    """
    store = _run_status_store
    for stage_def in DEMO_STAGES:
        record = store.set_stage(
            run_id=run_id,
            stage=stage_def["stage"],
            label=stage_def["label"],
            pct=stage_def["pct"],
        )
        payload = json.dumps(record)
        yield f"event: run.progress\ndata: {payload}\n\n"
        if stage_def["stage"] != "DONE":
            await asyncio.sleep(0.05)  # minimal delay, deterministic


# ---------------------------------------------------------------------------
# SSE generators for activity and presence streams (v4.2)
# ---------------------------------------------------------------------------

from activity_stream import get_activity_store
from presence import get_presence_store


async def activity_stream_generator(workspace_id: Optional[str] = None) -> AsyncGenerator[str, None]:
    """
    In DEMO mode: emit all existing activity events then a sentinel.
    """
    store = get_activity_store()
    events = store.list(workspace_id=workspace_id, limit=50)
    # Emit oldest first (reversed from list which returns newest-first)
    for ev in reversed(events):
        payload = json.dumps(ev)
        yield f"event: activity.event\ndata: {payload}\n\n"
        await asyncio.sleep(0.02)
    # Sentinel: connected
    yield f"event: activity.connected\ndata: {{\"status\": \"live\"}}\n\n"


async def presence_stream_generator(workspace_id: Optional[str] = None) -> AsyncGenerator[str, None]:
    """
    In DEMO mode: emit current presence state then sentinel.
    """
    store = get_presence_store()
    records = store.list(workspace_id=workspace_id)
    for rec in records:
        payload = json.dumps(rec)
        yield f"event: presence.update\ndata: {payload}\n\n"
        await asyncio.sleep(0.01)
    yield f"event: presence.connected\ndata: {{\"status\": \"live\"}}\n\n"


# ---------------------------------------------------------------------------
# FastAPI router
# ---------------------------------------------------------------------------

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse, JSONResponse

live_run_router = APIRouter(tags=["live-run"])


@live_run_router.get("/events/run-progress")
async def sse_run_progress(run_id: str = Query(...)) -> StreamingResponse:
    """SSE stream for deterministic run progress (DEMO)."""
    return StreamingResponse(
        run_progress_generator(run_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@live_run_router.get("/events/activity")
async def sse_activity(workspace_id: Optional[str] = Query(None)) -> StreamingResponse:
    """SSE stream for activity events (DEMO replay)."""
    return StreamingResponse(
        activity_stream_generator(workspace_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@live_run_router.get("/events/presence")
async def sse_presence(workspace_id: Optional[str] = Query(None)) -> StreamingResponse:
    """SSE stream for presence changes (DEMO replay)."""
    return StreamingResponse(
        presence_stream_generator(workspace_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@live_run_router.get("/runs/{run_id}/status")
def get_run_status(run_id: str) -> JSONResponse:
    """Get current run status/stage/pct (deterministic in DEMO)."""
    record = _run_status_store.get(run_id)
    if record is None:
        record = {
            "run_id": run_id,
            "stage": "NOT_STARTED",
            "label": "Not started",
            "pct": 0,
            "done": False,
            "status_hash": hashlib.sha256(run_id.encode()).hexdigest(),
        }
    return JSONResponse(record)
