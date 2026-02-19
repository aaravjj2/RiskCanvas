# Reviews — Wave 51

## Overview

The Reviews module implements a formal review state machine for portfolio decisions. Reviews progress through defined states and produce tamper-evident decision hashes.

## State Machine

```
DRAFT → (submit) → IN_REVIEW → (decide: approve) → APPROVED
                              → (decide: reject)  → REJECTED
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/reviews` | List reviews (`?status=`, `?limit=`) |
| `POST` | `/reviews` | Create review |
| `GET` | `/reviews/{id}` | Get review |
| `POST` | `/reviews/{id}/submit` | Advance DRAFT → IN_REVIEW |
| `POST` | `/reviews/{id}/decide` | Approve or reject (IN_REVIEW → APPROVED/REJECTED) |

### Create Request Body

```json
{
  "tenant_id": "tenant-001",
  "subject_type": "portfolio",
  "subject_id": "ptf-001",
  "title": "Q1 2026 Portfolio Review",
  "description": "Quarterly risk assessment",
  "created_by": "analyst@example.com"
}
```

### Decide Request Body

```json
{
  "decision": "APPROVED",
  "decided_by": "cro@example.com",
  "rationale": "All limits within bounds."
}
```

### Decide Response

```json
{
  "review": {
    "id": "rev-...",
    "status": "APPROVED",
    "decision": "APPROVED",
    "decided_by": "cro@example.com",
    "decision_hash": "sha256:abcd1234...",
    "decided_at": "2026-02-19T00:00:00Z"
  }
}
```

### Decision Hash

`decision_hash = SHA-256(id + decision + decided_by + decided_at + rationale)` — hex-encoded, prefixed `sha256:`.

## Frontend

**Route**: `/reviews`  
**Page**: `ReviewsPage.tsx`  
**Nav item**: `nav-reviews` (FileCheck2 icon)

### Key `data-testid` Values

| testid | Element |
|--------|---------|
| `reviews-page` | Page root |
| `reviews-table-ready` | After data loads |
| `review-row-{i}` | Table row |
| `review-drawer-ready` | Detail drawer |
| `review-decision-hash` | Decision hash display |
| `review-submit` | Submit button (DRAFT only) |
| `review-approve` | Approve button (IN_REVIEW only) |
| `review-reject` | Reject button (IN_REVIEW only) |

## Determinism

- ASOF: `2026-02-19T00:00:00Z`
- Decision hash is deterministic: same inputs → same hash
- State transitions are irreversible (APPROVED/REJECTED are terminal)
