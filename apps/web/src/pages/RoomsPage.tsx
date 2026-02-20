/**
 * RoomsPage.tsx (v5.55.0 — Wave 66)
 * Route: /rooms
 *
 * Decision Rooms v1 — collaboration hub for pinning evidence, locking decisions,
 * and checking policy gate verdicts.
 *
 * data-testids:
 *   rooms-page, rooms-ready, room-row-{i}, room-open-{room_id},
 *   room-drawer, room-pin-btn, room-lock-btn, room-notes-input,
 *   room-decision-gate-badge, room-decision-gate-open,
 *   room-create-btn, room-status-badge-{status},
 *   room-timeline-list, room-timeline-item-{i}
 */
import { useState, useEffect, useCallback } from "react";
import PageShell from "@/components/ui/PageShell";
import RightDrawer from "@/components/ui/RightDrawer";
import { useToast } from "@/components/ui/ToastCenter";

const API = (path: string) => `/api${path}`;

type RoomStatus = "OPEN" | "LOCKED" | "ARCHIVED";

interface Room {
  room_id: string;
  name: string;
  status: RoomStatus;
  tenant_id: string;
  pinned_entities: string[];
  notes: string[];
  attestations: string[];
  created_at: string;
  updated_at: string;
  locked_at?: string;
  graph_head_hash?: string;
}

interface GateVerdict {
  verdict: "ALLOW" | "BLOCK" | "CONDITIONAL";
  reasons: string[];
  required: string[];
  evaluated_at: string;
}

interface TimelineEvent {
  event_id: string;
  event_type: string;
  actor: string;
  description: string;
  metadata?: Record<string, unknown>;
  timestamp: string;
}

const STATUS_COLORS: Record<RoomStatus, string> = {
  OPEN:     "bg-green-900/40 text-green-300 border-green-700/40",
  LOCKED:   "bg-orange-900/40 text-orange-300 border-orange-700/40",
  ARCHIVED: "bg-gray-800/40 text-gray-400 border-gray-700/40",
};

const VERDICT_COLORS: Record<string, string> = {
  ALLOW:       "bg-green-900/40 text-green-300 border-green-700/40",
  BLOCK:       "bg-red-900/40 text-red-300 border-red-700/40",
  CONDITIONAL: "bg-yellow-900/40 text-yellow-300 border-yellow-700/40",
};

export default function RoomsPage() {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedRoom, setSelectedRoom] = useState<Room | null>(null);
  const [gate, setGate] = useState<GateVerdict | null>(null);
  const [gateAction, setGateAction] = useState<string>("room.lock");
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);

  const [pinInput, setPinInput] = useState("");
  const [noteInput, setNoteInput] = useState("");

  const [creating, setCreating] = useState(false);
  const [newRoomName, setNewRoomName] = useState("");

  // v5.58.1 depth wave additions
  const [policyV3, setPolicyV3] = useState<any>(null);
  const [policyV3Loading, setPolicyV3Loading] = useState(false);
  const [explainOpen, setExplainOpen] = useState(false);
  const [explanation, setExplanation] = useState<any>(null);
  const [explainLoading, setExplainLoading] = useState(false);
  const [seedLoading, setSeedLoading] = useState(false);
  const [seedResult, setSeedResult] = useState<{ dataset_id: string; scenario_id: string; run_id: string; eval_id: string; review_id: string } | null>(null);

  const { addToast } = useToast();
  const toast = (opts: { title: string; description?: string; variant?: string }) =>
    addToast(opts.description ? `${opts.title}: ${opts.description}` : opts.title,
      opts.variant === "destructive" ? "error" : opts.variant === "success" ? "success" : "info");

  const loadRooms = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(API("/rooms"));
      if (!res.ok) throw new Error("Failed to load rooms");
      const data = await res.json();
      setRooms(data.rooms ?? []);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadRooms(); }, [loadRooms]);

  // Keyboard nav: ESC closes drawer
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setSelectedRoom(null);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const openRoom = async (room: Room) => {
    setSelectedRoom(room);
    setGate(null);
    // Load timeline
    try {
      const res = await fetch(API(`/rooms/${room.room_id}/timeline`));
      if (res.ok) {
        const data = await res.json();
        setTimeline(data.events ?? []);
      }
    } catch {}
  };

  const handlePin = async () => {
    if (!selectedRoom || !pinInput.trim()) return;
    try {
      const res = await fetch(API(`/rooms/${selectedRoom.room_id}/pin`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ entity_id: pinInput.trim(), note: noteInput.trim() || undefined }),
      });
      if (!res.ok) throw new Error("Pin failed");
      const data = await res.json();
      toast({ title: "Pinned", description: `Entity ${pinInput.trim()} pinned`, variant: "success" });
      setPinInput("");
      setNoteInput("");
      setSelectedRoom(data.room);
    } catch (e) {
      toast({ title: "Pin failed", description: String(e), variant: "destructive" });
    }
  };

  const handleLock = async () => {
    if (!selectedRoom) return;
    toast({ title: "Checking policy gate...", description: "", variant: "default" });
    // Check gate first
    try {
      const gateRes = await fetch(API("/policy/decision-gate"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "room.lock", room_id: selectedRoom.room_id }),
      });
      const gateData = await gateRes.json();
      setGate(gateData);
      if (gateData.verdict === "BLOCK") {
        toast({ title: "BLOCKED by policy gate", description: gateData.reasons?.join("; "), variant: "destructive" });
        return;
      }
    } catch {}

    try {
      const res = await fetch(API(`/rooms/${selectedRoom.room_id}/lock`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail ?? "Lock failed");
      }
      const data = await res.json();
      toast({ title: "Room locked", description: `graph_head: ${data.room?.graph_head_hash?.slice(0, 12)}`, variant: "success" });
      setSelectedRoom(data.room);
      await loadRooms();
    } catch (e) {
      toast({ title: "Lock failed", description: String(e), variant: "destructive" });
    }
  };

  const checkGate = async (action: string) => {
    if (!selectedRoom) return;
    setGate(null);
    try {
      const res = await fetch(API("/policy/decision-gate"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, room_id: selectedRoom.room_id }),
      });
      const data = await res.json();
      setGate(data);
    } catch (e) {
      toast({ title: "Gate check failed", description: String(e), variant: "destructive" });
    }
  };

  const checkPolicyV3 = async (room: Room) => {
    setPolicyV3Loading(true);
    setPolicyV3(null);
    try {
      const res = await fetch(API("/policy/v3/decision"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          subject_type: "room",
          subject_id: room.room_id,
          checks: ["approved_review", "attestation_chain", "eval_stability"],
          context: { room_id: room.room_id },
        }),
      });
      if (!res.ok) throw new Error(`${res.status}`);
      const data = await res.json();
      setPolicyV3(data.decision);
    } catch (e) {
      toast({ title: "Policy V3 check failed", description: String(e), variant: "destructive" });
    } finally {
      setPolicyV3Loading(false);
    }
  };

  const loadExplanation = async (room: Room) => {
    setExplainLoading(true);
    setExplanation(null);
    try {
      const body: Record<string, string> = {};
      if (seedResult) {
        body.dataset_id = seedResult.dataset_id;
        body.scenario_id = seedResult.scenario_id;
        body.run_id = seedResult.run_id;
        body.review_id = seedResult.review_id;
      } else {
        body.dataset_id = room.room_id; // fallback: use room_id as subject
      }
      const res = await fetch(API("/explain/verdict"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`${res.status}`);
      const data = await res.json();
      setExplanation(data.explanation);
      setExplainOpen(true);
    } catch (e) {
      toast({ title: "Explain failed", description: String(e), variant: "destructive" });
    } finally {
      setExplainLoading(false);
    }
  };

  const demoQuickStart = async () => {
    setSeedLoading(true);
    setSeedResult(null);
    try {
      // 1. Ingest dataset
      const dsRes = await fetch(API("/datasets/ingest"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          kind: "portfolio", name: "Rooms Demo Portfolio",
          payload: { positions: [
            { ticker: "AAPL", quantity: 100, cost_basis: 178.5 },
            { ticker: "MSFT", quantity: 50,  cost_basis: 415.0 },
          ]},
          created_by: "demo@rc.io",
        }),
      });
      const dsData = await dsRes.json();
      const datasetId = dsData.dataset?.dataset_id;

      // 2. Create scenario
      const scRes = await fetch(API("/scenarios-v2"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: "Rooms Demo Stress", kind: "stress",
          payload: { shock_pct: 0.15, apply_to: ["equity"] },
          created_by: "demo@rc.io",
        }),
      });
      const scData = await scRes.json();
      const scenarioId = scData.scenario?.scenario_id;

      // 3. Run scenario
      const runRes = await fetch(API(`/scenarios-v2/${scenarioId}/run`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ triggered_by: "demo@rc.io" }),
      });
      const runData = await runRes.json();
      const runId = runData.run?.run_id;

      // 4. Run eval
      const evalRes = await fetch(API("/eval/v3/run"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ run_ids: [runId ?? "demo-run-seed"] }),
      });
      const evalData = await evalRes.json();
      const evalId = evalData.eval?.eval_id;

      // 5. Create review draft
      const rvRes = await fetch(API("/reviews"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          subject_type: "dataset", subject_id: datasetId ?? "demo-ds",
          created_by: "demo@rc.io", notes: "Demo Quick Start review",
        }),
      });
      const rvData = await rvRes.json();
      const reviewId = rvData.review?.review_id;

      // 6. Create a room
      const rmRes = await fetch(API("/rooms"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: "Demo Quick Start Room" }),
      });
      const rmData = await rmRes.json();

      setSeedResult({ dataset_id: datasetId, scenario_id: scenarioId, run_id: runId, eval_id: evalId, review_id: reviewId });
      toast({ title: "Quick Start seeded", description: "Dataset → Scenario → Run → Eval → Review created", variant: "success" });
      await loadRooms();

      // Open the new room
      if (rmData.room) openRoom(rmData.room);
    } catch (e) {
      toast({ title: "Quick Start failed", description: String(e), variant: "destructive" });
    } finally {
      setSeedLoading(false);
    }
  };

  const createRoom = async () => {
    if (!newRoomName.trim()) return;
    try {
      const res = await fetch(API("/rooms"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newRoomName.trim() }),
      });
      if (!res.ok) throw new Error("Create failed");
      toast({ title: "Room created", variant: "success" });
      setNewRoomName("");
      setCreating(false);
      await loadRooms();
    } catch (e) {
      toast({ title: "Create failed", description: String(e), variant: "destructive" });
    }
  };

  return (
    <PageShell
      title="Decision Rooms"
      subtitle="v5.58.1 — Home"
      actions={
        <>
          <button
            onClick={loadRooms}
            className="px-3 py-1.5 text-xs rounded bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 transition"
            data-testid="rooms-refresh-btn"
          >
            Refresh
          </button>
          <button
            onClick={demoQuickStart}
            disabled={seedLoading}
            className="px-3 py-1.5 text-xs rounded bg-green-700/80 hover:bg-green-600 text-white transition disabled:opacity-50"
            data-testid="rooms-demo-quickstart"
          >
            {seedLoading ? "Seeding…" : "Demo Quick Start"}
          </button>
          <button
            onClick={() => setCreating(true)}
            className="px-3 py-1.5 text-xs rounded bg-primary hover:bg-primary/90 text-primary-foreground transition"
            data-testid="room-create-btn"
          >
            + New Room
          </button>
        </>
      }
    >
      <div className="space-y-4" data-testid="rooms-page">
        {loading && (
          <div className="text-sm text-muted-foreground animate-pulse" data-testid="rooms-loading">
            Loading rooms…
          </div>
        )}
        {error && (
          <div className="rounded border border-red-700/50 bg-red-900/20 p-4 text-red-300 text-sm">
            {error}
          </div>
        )}

        {/* Create form */}
        {creating && (
          <div className="rounded border border-border bg-card p-4 flex gap-3 items-center" data-testid="room-create-form">
            <input
              value={newRoomName}
              onChange={e => setNewRoomName(e.target.value)}
              placeholder="Room name…"
              className="flex-1 text-sm bg-background border border-border rounded px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary"
              data-testid="room-name-input"
              onKeyDown={e => e.key === "Enter" && createRoom()}
              autoFocus
            />
            <button
              onClick={createRoom}
              className="px-3 py-1.5 text-xs rounded bg-primary text-primary-foreground hover:bg-primary/90 transition"
              data-testid="room-create-confirm-btn"
            >
              Create
            </button>
            <button
              onClick={() => { setCreating(false); setNewRoomName(""); }}
              className="px-3 py-1.5 text-xs rounded bg-muted text-muted-foreground hover:bg-muted/70 transition"
              data-testid="room-create-cancel-btn"
            >
              Cancel
            </button>
          </div>
        )}

        {/* Rooms table */}
        {!loading && rooms.length === 0 && (
          <div className="text-sm text-muted-foreground text-center py-12" data-testid="rooms-empty">
            No rooms yet. Create your first decision room.
          </div>
        )}

        {rooms.length > 0 && (
          <div className="rounded border border-border bg-card overflow-hidden" data-testid="rooms-ready">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/30 text-xs text-muted-foreground">
                  <th className="text-left px-4 py-2">Room</th>
                  <th className="text-left px-4 py-2">Status</th>
                  <th className="text-left px-4 py-2">Pinned</th>
                  <th className="text-left px-4 py-2">Notes</th>
                  <th className="text-left px-4 py-2">Updated</th>
                  <th></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/30">
                {rooms.map((room, i) => (
                  <tr
                    key={room.room_id}
                    className="hover:bg-muted/20 transition cursor-pointer"
                    onClick={() => openRoom(room)}
                    data-testid={`room-row-${i}`}
                    tabIndex={0}
                    onKeyDown={e => e.key === "Enter" && openRoom(room)}
                    role="button"
                  >
                    <td className="px-4 py-2">
                      <div className="font-medium">{room.name}</div>
                      <div className="text-xs text-muted-foreground font-mono">{room.room_id}</div>
                    </td>
                    <td className="px-4 py-2">
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full border font-medium ${STATUS_COLORS[room.status]}`}
                        data-testid={`room-status-badge-${room.status.toLowerCase()}`}
                      >
                        {room.status}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-xs text-muted-foreground">
                      {room.pinned_entities.length} entities
                    </td>
                    <td className="px-4 py-2 text-xs text-muted-foreground">
                      {room.notes.length} notes
                    </td>
                    <td className="px-4 py-2 text-xs text-muted-foreground font-mono">
                      {(room.updated_at ?? room.created_at)?.slice(0, 16) ?? "—"}
                    </td>
                    <td className="px-4 py-2">
                      <button
                        onClick={e => { e.stopPropagation(); openRoom(room); }}
                        className="text-xs text-primary hover:underline"
                        data-testid={`room-open-${room.room_id}`}
                      >
                        Open →
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Room Detail Drawer */}
      <RightDrawer
        open={selectedRoom !== null}
        onClose={() => { setSelectedRoom(null); setGate(null); }}
        title={selectedRoom?.name ?? "Room"}
        headerActions={
          selectedRoom && (
            <span className={`text-xs px-2 py-0.5 rounded-full border ${STATUS_COLORS[selectedRoom.status]}`}>
              {selectedRoom.status}
            </span>
          )
        }
      >
        {selectedRoom && (
          <div className="space-y-5 p-4" data-testid="room-drawer">
            {/* Room ID */}
            <div>
              <span className="text-xs text-muted-foreground">Room ID</span>
              <p className="text-sm font-mono mt-0.5">{selectedRoom.room_id}</p>
            </div>

            {/* Pin entity section */}
            {selectedRoom.status === "OPEN" && (
              <div>
                <h3 className="text-sm font-semibold mb-2">Pin Entity</h3>
                <div className="space-y-2">
                  <input
                    value={pinInput}
                    onChange={e => setPinInput(e.target.value)}
                    placeholder="Entity ID to pin…"
                    className="w-full text-xs bg-background border border-border rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary"
                    data-testid="room-pin-input"
                  />
                  <input
                    value={noteInput}
                    onChange={e => setNoteInput(e.target.value)}
                    placeholder="Note (optional)…"
                    className="w-full text-xs bg-background border border-border rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary"
                    data-testid="room-notes-input"
                  />
                  <button
                    onClick={handlePin}
                    disabled={!pinInput.trim()}
                    className="px-3 py-1.5 text-xs rounded bg-primary text-primary-foreground hover:bg-primary/90 transition disabled:opacity-40"
                    data-testid="room-pin-btn"
                  >
                    Pin Entity
                  </button>
                </div>
              </div>
            )}

            {/* Pinned entities */}
            {selectedRoom.pinned_entities.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold mb-2">
                  Pinned Entities ({selectedRoom.pinned_entities.length})
                </h3>
                <div className="space-y-1">
                  {selectedRoom.pinned_entities.map(eid => (
                    <div key={eid} className="text-xs font-mono px-2 py-1 rounded bg-muted/30">
                      {eid}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Lock actions */}
            {selectedRoom.status === "OPEN" && (
              <div>
                <h3 className="text-sm font-semibold mb-2">Actions</h3>
                <div className="flex gap-2">
                  <button
                    onClick={handleLock}
                    className="px-3 py-1.5 text-xs rounded bg-orange-700/50 text-orange-200 hover:bg-orange-700/80 border border-orange-700/50 transition"
                    data-testid="room-lock-btn"
                  >
                    Lock Room
                  </button>
                </div>
              </div>
            )}

            {selectedRoom.locked_at && (
              <div>
                <span className="text-xs text-muted-foreground">Locked at</span>
                <p className="text-xs font-mono mt-0.5">{selectedRoom.locked_at}</p>
                {selectedRoom.graph_head_hash && (
                  <>
                    <span className="text-xs text-muted-foreground">Graph head hash</span>
                    <p className="text-xs font-mono mt-0.5 break-all">{selectedRoom.graph_head_hash}</p>
                  </>
                )}
              </div>
            )}

            {/* Policy Gate v3 (Depth Wave) */}
            <div data-testid="policy-v3-card">
              <h3 className="text-sm font-semibold mb-2">Policy Gate v3</h3>
              <button
                onClick={() => checkPolicyV3(selectedRoom)}
                disabled={policyV3Loading}
                className="px-3 py-1.5 text-xs rounded bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 transition disabled:opacity-50"
                data-testid="policy-v3-check-btn"
              >
                {policyV3Loading ? "Checking…" : "Check Policy v3"}
              </button>
              {policyV3 && (
                <div className="mt-2 space-y-2">
                  <div
                    data-testid="policy-v3-verdict"
                    className={`text-sm font-bold px-3 py-2 rounded ${
                      policyV3.verdict === "SHIP" ? "bg-green-900/30 text-green-300" :
                      policyV3.verdict === "CONDITIONAL" ? "bg-yellow-900/30 text-yellow-300" :
                      "bg-red-900/30 text-red-300"
                    }`}
                  >
                    {policyV3.verdict}
                    <span className="text-xs font-normal ml-2 opacity-60">
                      {policyV3.checks_passed}/{policyV3.checks_run} checks passed
                    </span>
                  </div>
                  {policyV3.reasons?.map((r: any, i: number) => (
                    <div
                      key={i}
                      data-testid={`policy-v3-reason-${i}`}
                      className={`text-xs px-2 py-1.5 rounded border ${
                        r.passed ? "border-green-700/30 bg-green-900/10 text-green-300" : "border-red-700/30 bg-red-900/10 text-red-300"
                      }`}
                    >
                      <span className="font-medium">{r.check}:</span> {r.reason}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Explain drawer trigger */}
            <div>
              <h3 className="text-sm font-semibold mb-2">Explainability</h3>
              <button
                onClick={() => loadExplanation(selectedRoom)}
                disabled={explainLoading}
                className="px-3 py-1.5 text-xs rounded bg-blue-700/30 hover:bg-blue-700/50 text-blue-300 border border-blue-700/30 transition disabled:opacity-50"
                data-testid="explain-open"
              >
                {explainLoading ? "Loading…" : "Why this verdict?"}
              </button>
            </div>

            {/* Policy Decision Gate (legacy) */}
            <div>
              <h3 className="text-sm font-semibold mb-2">Policy Decision Gate</h3>
              <div className="flex gap-2 mb-2">
                <select
                  value={gateAction}
                  onChange={e => setGateAction(e.target.value)}
                  className="text-xs bg-card border border-border rounded px-2 py-1"
                  data-testid="room-gate-action-select"
                >
                  <option value="room.lock">room.lock</option>
                  <option value="export.decision_packet">export.decision_packet</option>
                </select>
                <button
                  onClick={() => checkGate(gateAction)}
                  className="px-3 py-1.5 text-xs rounded bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 transition"
                  data-testid="room-decision-gate-open"
                >
                  Check Gate
                </button>
              </div>
              {gate && (
                <div
                  className={`rounded border p-3 space-y-1 ${VERDICT_COLORS[gate.verdict]}`}
                  data-testid="room-decision-gate-badge"
                >
                  <div className="font-bold text-sm">{gate.verdict}</div>
                  {gate.reasons.map((r, i) => (
                    <div key={i} className="text-xs">{r}</div>
                  ))}
                </div>
              )}
            </div>

            {/* Timeline */}
            {timeline.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold mb-2">Timeline ({timeline.length})</h3>
                <div className="space-y-2" data-testid="room-timeline-list">
                  {timeline.map((ev, i) => (
                    <div
                      key={ev.event_id}
                      className="text-xs p-2 rounded bg-muted/20 border border-border/30"
                      data-testid={`room-timeline-item-${i}`}
                    >
                      <div className="flex justify-between">
                        <span className="font-medium">{ev.event_type}</span>
                        <span className="text-muted-foreground font-mono">{ev.timestamp.slice(0, 16)}</span>
                      </div>
                      <div className="text-muted-foreground mt-0.5">{ev.description}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </RightDrawer>

      {/* Explanation Drawer */}
      <RightDrawer
        open={explainOpen}
        onClose={() => { setExplainOpen(false); setExplanation(null); }}
        title="Why this verdict?"
      >
        {explanation && (
          <div className="space-y-4 p-4">
            <div className="text-xs font-mono text-muted-foreground break-all">
              {explanation.explain_id}
            </div>
            <div className="text-xs text-muted-foreground italic">
              {explanation.note}
            </div>
            <div className="space-y-2">
              <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Reasons ({explanation.reason_count})
              </div>
              {explanation.reasons?.map((r: any, i: number) => (
                <div
                  key={i}
                  data-testid={`explain-reason-${i}`}
                  className="bg-muted/20 rounded p-2 border border-border/30 space-y-1"
                >
                  <div className="text-xs font-medium text-white">{r.title}</div>
                  <div className="text-xs text-muted-foreground">{r.text}</div>
                  {r.node_ref && (
                    <div
                      data-testid={`explain-link-${i}`}
                      className="text-xs font-mono text-blue-400"
                    >
                      ↗ {r.node_ref}
                    </div>
                  )}
                </div>
              ))}
            </div>
            {explanation.evidence_refs?.length > 0 && (
              <div>
                <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
                  Evidence Links
                </div>
                {explanation.evidence_refs.map((ref: any, i: number) => (
                  <div
                    key={i}
                    data-testid={`explain-link-${i + (explanation.reasons?.length ?? 0)}`}
                    className="text-xs font-mono text-blue-400 bg-muted/20 rounded px-2 py-1 mb-1"
                  >
                    {ref.entity_type}: {ref.entity_id?.slice(0, 20)}…
                    <span className="text-muted-foreground ml-2">→ {ref.node_id}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </RightDrawer>
    </PageShell>
  );
}
