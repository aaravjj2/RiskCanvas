# RiskCanvas — DigitalOcean Submission
## Wave 33-40 Mega Delivery · v4.97.0

### Project Overview

RiskCanvas is a full-stack risk analytics platform deployable on DigitalOcean
App Platform. Wave 33-40 delivers a complete UI/UX system with 9 new reusable
UI primitives, 2 new feature pages, and a comprehensive automated test suite.

### Wave 33-40 Deliverables

| Wave | Component | Lines | Tests |
|------|-----------|-------|-------|
| 33 | PageShell, DataTable, RightDrawer, ToastCenter, EmptyStatePanel, LoadingSkeleton, ErrorPanel, ProgressBanner, PresentationMode | ~850 | 18 E2E |
| 34 | ExportsHubPage + exports_hub.py backend | ~350 | 12 pytest + 12 E2E |
| 35 | Presentation Mode 3-rail system | included in 33 | 9 E2E |
| 36 | invariants_check.py + testid_catalog.py | ~200 | 6 pytest |
| 37 | WorkbenchPage (3-panel layout) | ~250 | 14 E2E |
| 38 | Micro-UX copy buttons & bulk actions | included | 12 E2E |
| 39 | phase39-ui-judge-demo.spec.ts | ~340 | 21 E2E |
| 40 | judge_mode_w33_40.py + tests | ~180 | 15 pytest |

### Deployment on DigitalOcean

```yaml
# app.yaml (sample)
name: riskcanvas
services:
  - name: api
    image:
      registry_type: DOCKER_HUB
    http_port: 8090
    run_command: uvicorn main:app --host 0.0.0.0 --port 8090
    envs:
      - key: PORT
        value: "8090"

  - name: web
    image:
      registry_type: DOCKER_HUB
    http_port: 4177
    run_command: npx vite preview --port 4177 --host 0.0.0.0
```

### PresentationMode — DigitalOcean Rail

The DigitalOcean presentation rail provides a 5-step guided demo:
1. **Dashboard** — Real-time risk metrics and KPIs
2. **Workbench** — Unified analytics workspace
3. **Exports Hub** — Audit pack management
4. **Incident Playbooks** — SRE runbooks and escalation
5. **Readiness Check** — Deployment readiness scoring

### Test Results

```
pytest:            905 passed, 0 failed (5.60s)
Playwright unit:    62 passed, 0 failed (16.7s)
Playwright judge:   21 passed, 0 failed
Screenshots:        91 proof images (≥55 required)
```

### Key APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check → `{"status":"healthy","version":"4.9.0"}` |
| `/exports/recent` | GET | 5 demo export packs with SHA-256 |
| `/exports/verify/{pack_id}` | GET | Verify pack integrity |
| `/judge/w33-40/generate-pack` | POST | Generate proof pack (verdict: PASS) |
| `/judge/w33-40/files` | GET | List 26 proof files |

---
*Prepared: 2026-02-19 · RiskCanvas v4.97.0 · Wave 33-40 Mega Delivery*
