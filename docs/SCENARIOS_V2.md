# Scenario Composer v2 — Wave 50

## Overview

Scenario Composer v2 introduces first-class scenario objects with deterministic run/replay capability. Each scenario stores its configuration, and runs produce deterministic impact assessments.

## Scenario Kinds

| Kind | Impact Fields |
|------|--------------|
| `rate_shock` | `parallel_shift`, `pnl_estimate`, `duration_impact` |
| `credit_event` | `pnl_estimate`, `spread_widening`, `affected_positions` |
| `fx_move` | `pnl_estimate`, `fx_sensitivity`, `hedge_cost` |
| `stress_test` | `pnl_estimate`, `var_impact`, `tail_loss` |
| `liquidity_crisis` | `pnl_estimate`, `liquidity_gap`, `funding_cost` |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/scenarios-v2` | List scenarios (`?kind=`, `?limit=`) |
| `POST` | `/scenarios-v2` | Create scenario |
| `GET` | `/scenarios-v2/{id}` | Get scenario |
| `POST` | `/scenarios-v2/{id}/run` | Execute scenario run |
| `POST` | `/scenarios-v2/{id}/replay` | Replay with identical run_id |
| `GET` | `/scenarios-v2/{id}/runs` | List runs for scenario |
| `GET` | `/scenarios-v2/templates/all` | Scenario templates |

### Create Request Body

```json
{
  "tenant_id": "tenant-001",
  "kind": "rate_shock",
  "name": "Fed +100bp",
  "payload": { "shock_bps": 100, "curve": "USD_LIBOR" },
  "created_by": "user@example.com"
}
```

### Run Response

```json
{
  "run_id": "run-...",
  "scenario_id": "scn-...",
  "status": "completed",
  "impact": {
    "parallel_shift": 100,
    "pnl_estimate": -145000.0,
    "duration_impact": -2.83
  },
  "run_at": "2026-02-19T00:00:00Z"
}
```

### Replay

`POST /scenarios-v2/{id}/replay` accepts optional `{"run_id": "run-..."}` to replay a specific run. Same `run_id` → identical `impact` (deterministic).

## Frontend

**Route**: `/scenario-composer`  
**Page**: `ScenarioComposerPage.tsx`  
**Nav item**: `nav-scenario-composer` (Layers icon)

### Key `data-testid` Values

| testid | Element |
|--------|---------|
| `scenario-composer` | Page root |
| `scenario-list-ready` | After scenario list loads |
| `scenario-row-{i}` | Scenario table row |
| `scenario-kind-select` | Kind selector |
| `scenario-validate` | Validate payload |
| `scenario-run` | Execute run |
| `scenario-replay` | Replay run |
| `scenario-preview-ready` | Preview panel |
| `scenario-action-log` | Action log panel |

## Determinism

- ASOF: `2026-02-19T00:00:00Z`
- `_compute_impact(kind, payload)` is a pure function — same kind + payload → same impact values
- `replay_scenario()` always returns the same impact as the original run
