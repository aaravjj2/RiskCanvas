# Decision Packets — Wave 51-52

## Overview

Decision Packets bundle a subject (portfolio, scenario, dataset) with all associated evidence into a 5-file tamper-evident archive. Each packet produces a manifest hash that chains all file hashes, ensuring integrity.

## Packet Structure

```
decision-packet-{id}/
├── subject.json          # Subject entity (portfolio/scenario/dataset)
├── runs.json             # Associated scenario runs
├── attestations.json     # Attestation chain
├── reviews.json          # Review decisions
├── summary.json          # Human-readable summary
└── MANIFEST.json         # SHA-256 of each file + manifest_hash
```

### manifest_hash

`manifest_hash = SHA-256(subject_hash + runs_hash + attestations_hash + reviews_hash + summary_hash)`

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/exports/decision-packet` | Generate packet |
| `GET` | `/exports/decision-packets` | List packets |
| `GET` | `/exports/decision-packets/{id}` | Get packet |
| `POST` | `/exports/decision-packets/{id}/verify` | Verify manifest hash |

### Generate Request Body

```json
{
  "tenant_id": "tenant-001",
  "subject_type": "portfolio",
  "subject_id": "ptf-001"
}
```

### Generate Response

```json
{
  "packet": {
    "id": "pkt-...",
    "tenant_id": "tenant-001",
    "subject_type": "portfolio",
    "subject_id": "ptf-001",
    "status": "complete",
    "manifest_hash": "sha256:abcd1234...",
    "files": {
      "subject": "subject.json",
      "runs": "runs.json",
      "attestations": "attestations.json",
      "reviews": "reviews.json",
      "summary": "summary.json",
      "manifest": "MANIFEST.json"
    },
    "created_at": "2026-02-19T00:00:00Z"
  }
}
```

### Verify Response

```json
{
  "packet_id": "pkt-...",
  "verified": true,
  "manifest_hash": "sha256:abcd1234...",
  "recomputed_hash": "sha256:abcd1234...",
  "verified_at": "2026-02-19T00:00:00Z"
}
```

## Usage

Decision Packets are the primary evidence artifact for:

1. **Audit trails** — Immutable record of who approved what, when
2. **Regulatory submission** — Self-contained evidence bundle
3. **Judge Mode** — Input to judge_mode_v3 evaluation packs

## Determinism

- ASOF: `2026-02-19T00:00:00Z`
- `generate_decision_packet()` with same inputs → same `manifest_hash`
- Verify always re-computes and compares — same inputs → `verified: true`
