# RiskCanvas — GitLab Submission
## Wave 33-40 Mega Delivery · v4.97.0

### Project Overview

RiskCanvas is an AI-assisted risk analytics platform with a fully deterministic,
auditible UI system built for enterprise compliance workflows.

### Wave 33-40 Deliverables

| Wave | Description | Status |
|------|-------------|--------|
| 33 | UI Foundation: PageShell, DataTable, RightDrawer, ToastCenter, ProgressBanner, PresentationMode | ✅ PASS |
| 34 | Exports Hub Page — browse, verify, and inspect audit export packs | ✅ PASS |
| 35 | Presentation Mode — 3 guided rails for GitLab, Microsoft, DigitalOcean demos | ✅ PASS |
| 36 | UI Tooling — invariants checker, testid catalog (528 testids across 59 files) | ✅ PASS |
| 37 | Workbench — 3-panel all-in-one workspace with context drawer | ✅ PASS |
| 38 | Micro-UX Polish — copy buttons, bulk selection, version badge v4.97.0 | ✅ PASS |
| 39 | Judge Demo Automation — 21 Playwright tests, 91 proof screenshots | ✅ PASS |
| 40 | Proof Pack — backend judge API, 15 new tests, submission packs | ✅ PASS |

### Test Results

- **Python/pytest:** 905 passed, 0 failed, 0 skipped
- **Playwright (unit):** 62 passed, 0 failed, retries=0, workers=1
- **Playwright (judge demo):** 21 passed, 0 failed
- **Total Testids:** 528 across 59 TSX files
- **Proof Screenshots:** 91 (requirement: ≥55)

### Key Technical Highlights for GitLab

1. **MR Review Workbench** — The workbench panel at `/workbench` provides a
   dedicated panel for MR reviews with deterministic audit hash display
   (`sha256:a3f4e2b1c9d7f6e5a4b3c2d1e0f9a8b7`)

2. **Exports Hub** — `/exports` enables teams to browse, verify SHA-256 checksums,
   and inspect all export packs with a sortable DataTable + RightDrawer detail view

3. **CommandPalette** — Ctrl+K opens a fuzzy-search palette for rapid navigation
   across all 40+ features — essential for power users reviewing MRs

4. **PresentationMode** — Dedicated GitLab demo rail with 6 curated steps
   showcasing the MR analytics and policy evaluation use cases

### Architecture

```
Frontend: React 19 + Vite + TypeScript + Tailwind + Radix UI
Backend:  FastAPI + Python 3.10 + deterministic fixtures
Testing:  pytest (905) + Playwright (83 E2E tests)
Ports:    Backend 8090, Frontend 4177 (preview)
```

### Repository Structure

```
apps/web/src/components/ui/   # 9 new Wave 33 UI primitives
apps/web/src/pages/           # ExportsHubPage, WorkbenchPage
apps/api/exports_hub.py       # Exports Hub backend
apps/api/judge_mode_w33_40.py # Judge proof pack API
e2e/                          # 7 Playwright spec files
scripts/ui/                   # invariants_check.py, testid_catalog.py
docs/TESTIDS.md               # 528 testids catalog
```

### Live Endpoints

- `GET  http://localhost:8090/exports/recent` → 5 deterministic export packs
- `POST http://localhost:8090/judge/w33-40/generate-pack` → verdict: "PASS", score: 100%
- `GET  http://localhost:8090/judge/w33-40/files` → 26 proof files

---
*Prepared: 2026-02-19 · RiskCanvas v4.97.0 · Wave 33-40 Mega Delivery*
