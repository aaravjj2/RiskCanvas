# Datasets — Wave 49

## Overview

Dataset Ingestion v1 provides typed, validated dataset storage for portfolio analytics. Five dataset kinds are supported, each with schema validation.

## Dataset Kinds

| Kind | Description | Required Keys |
|------|-------------|---------------|
| `portfolio` | Portfolio positions | `positions` (list) |
| `rates_curve` | Interest rate curves | `curve` (list of `{tenor, rate}`) |
| `stress_preset` | Stress scenario config | `shocks` (dict) |
| `fx_set` | FX rate matrix | `pairs` (list of `{from, to, rate}`) |
| `credit_curve` | Credit/CDS spreads | `spreads` (list of `{tenor, spread}`) |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/datasets` | List datasets (optional `?kind=` filter, `?limit=`) |
| `GET` | `/datasets/{id}` | Get single dataset |
| `POST` | `/datasets/ingest` | Ingest + validate dataset |
| `POST` | `/datasets/validate` | Validate without persisting |

### Ingest Request Body

```json
{
  "tenant_id": "tenant-001",
  "kind": "portfolio",
  "name": "Q1 2026 Portfolio",
  "payload": { "positions": [...] },
  "created_by": "user@example.com"
}
```

### Ingest Response

```json
{
  "dataset": {
    "id": "ds-...",
    "tenant_id": "tenant-001",
    "kind": "portfolio",
    "name": "Q1 2026 Portfolio",
    "payload": {...},
    "validation_status": "valid",
    "errors": [],
    "created_by": "user@example.com",
    "created_at": "2026-02-19T00:00:00Z",
    "artifact_id": "art-..."
  },
  "errors": []
}
```

## Frontend

**Route**: `/datasets`  
**Page**: `DatasetsPage.tsx`  
**Nav item**: `nav-datasets` (Database icon)

### Key `data-testid` Values

| testid | Element |
|--------|---------|
| `datasets-page` | Page root |
| `datasets-table-ready` | After data loads |
| `dataset-row-{i}` | Table row |
| `dataset-kind-filter` | Kind select dropdown |
| `dataset-ingest-open` | Open ingest drawer |
| `dataset-drawer-ready` | Ingest drawer form |
| `dataset-validate-btn` | Validate payload |
| `dataset-save-btn` | Save dataset |

## Determinism

- ASOF constant: `2026-02-19T00:00:00Z`
- IDs are UUID4; demo seeds use fixed IDs (`ds-demo-001` through `ds-demo-006`)
- Validation is pure function: same payload → same `validation_status`
