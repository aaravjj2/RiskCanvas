# 2-Minute Demo Script — Wave 33-40 Mega Delivery

## Setup

```bash
# Ensure both servers are running:
# Backend: http://localhost:8090
# Frontend: http://localhost:4177
```

## Script (2 minutes)

### 00:00 — App Layout & Version Badge

> "RiskCanvas v4.97.0 — let me show you what we built in Wave 33-40."

1. Open http://localhost:4177
2. Point to version badge in sidebar: **v4.97.0**
3. Scroll sidebar to show new `Exports` and `Workbench` nav items

### 00:20 — Exports Hub

> "The Exports Hub gives teams full visibility into audit export packs."

4. Click `Exports` in sidebar → `/exports` loads
5. Show DataTable with 5 packs — sortable columns
6. Click a column header to demonstrate stable sort
7. Select 2 rows → bulk bar appears with count
8. Click `Details` on row 0 → RightDrawer opens with SHA-256
9. Click `Verify` inside drawer → toast notification fires
10. Press `ESC` → drawer closes

### 00:55 — Workbench

> "The Workbench is a unified 3-panel workspace."

11. Navigate to `/workbench`
12. Point to left panel (nav) / center panel (content) / action log
13. Click `Incidents` panel → content updates
14. Click `Context` → RightDrawer shows audit hash + copy button
15. Click copy → clipboard toast

### 01:25 — Presentation Mode

> "We built a guided demo mode for hackathon judges."

16. Click `Present` toggle in sidebar footer
17. Step card appears — show step title + progress indicator
18. Click `Next` twice
19. Switch to `DigitalOcean` rail → steps update

### 01:45 — Command Palette

> "Power users can navigate with Ctrl+K."

20. Press `Ctrl+K` → palette opens
21. Type `reports` → item highlighted
22. Press `Enter` → navigates instantly

### 01:55 — Close

> "905 pytest passing, 83 Playwright tests, 91 proof screenshots. All green."

---
*Timing: 2:00 ± 10 seconds*
