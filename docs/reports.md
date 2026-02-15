# Report Bundles (v1.2+)

## Overview

RiskCanvas v1.2 introduces deterministic, self-contained report bundles. Each bundle packages an analysis run into a portable format with embedded charts and canonical outputs.

## Report Bundle Structure

A report bundle consists of:

1. **report.html** — Self-contained HTML with inline CSS and SVG charts (no CDN dependencies)
2. **run.json** — Canonical JSON of all analysis outputs
3. **manifest.json** — Metadata with hashes and file links

## Report Bundle ID

```
report_bundle_id = SHA256(run_id + ":" + canonical_json(outputs))[:32]
```

**Properties**:
- Deterministic: same run → same bundle ID
- Content-addressable: hash includes all outputs
- Stable across regeneration if inputs unchanged

## API Endpoints

**Build report bundle**
```http
POST /reports/build
Body: { run_id }
Response: { report_bundle_id, run_id, portfolio_id, manifest }
```
- Fetches run data from database
- Generates HTML with embedded charts
- Creates manifest with all hashes
- Stores bundle in memory (or filesystem/S3 in production)
- Updates run record with `report_bundle_id`

**Get manifest**
```http
GET /reports/{report_bundle_id}/manifest
Response: {
  report_bundle_id,
  run_id,
  portfolio_id,
  engine_version,
  created_at,
  hashes: { output_hash, report_html_hash, run_json_hash },
  files: { report.html, run.json, manifest.json }
}
```

**Get HTML report**
```http
GET /reports/{report_bundle_id}/report.html
Response: HTML document (Content-Type: text/html)
```

**Get run JSON**
```http
GET /reports/{report_bundle_id}/run.json
Response: { pricing, greeks, var, scenarios }
```

## HTML Report Features

### Self-Contained
- All CSS inline (no external stylesheets)
- All charts as embedded SVG (no JavaScript libraries)
- No CDN dependencies (works offline)
- Single file distribution

### Deterministic Charts

**VaR Distribution Chart**
- Simple SVG bar chart
- Shows VaR 95% and VaR 99%
- Fixed dimensions (400x300)
- Normalized heights based on max value

**Portfolio Greeks Chart**
- SVG bar chart for delta, gamma, vega, theta
- Color-coded bars (delta: blue, gamma: green, vega: orange, theta: red)
- Values normalized for display

### Styling
- Clean, professional design
- Responsive layout (max-width: 1200px)
- Grid-based metrics cards
- Monospace hashes for technical data
- Print-friendly styles

### Content Sections
1. **Header** — Run ID, portfolio ID, engine version, timestamp
2. **Key Metrics** — Portfolio value, P&L, VaR 95%, VaR 99%
3. **Risk Distribution** — VaR chart
4. **Portfolio Greeks** — Greeks chart (if options present)
5. **Portfolio Positions** — Table of assets with symbol, type, quantity, price, value
6. **Footer** — RiskCanvas version, output hash

## Storage

**Current**: In-memory dictionary (`_report_bundles`)
- Fast access
- No persistence across restarts
- Suitable for demo/development

**Future**: Filesystem or S3
- Persistent storage
- Scalable for production
- Easy backup/restore

## Use Cases

### Audit Trail
- Generate report for each significant analysis
- Store report bundle alongside decision records
- Verify outputs via hash comparison

### Compliance
- Self-contained reports for regulatory submission
- No external dependencies (auditable)
- Includes all hashes for verification

### Sharing
- Download `report.html` for offline viewing
- Email/share single file (no broken links)
- Recipients can verify authenticity via hashes

### Reproducibility
- `run.json` contains canonical inputs/outputs
- Re-run analysis with same inputs → same hashes
- Detect any divergence via hash comparison

## Hash Verification

**Workflow**:
1. Client calls `POST /reports/build`
2. Server generates report and computes hashes:
   - `output_hash` — Hash of all analysis outputs
   - `report_html_hash` — Hash of generated HTML
   - `run_json_hash` — Hash of canonical run.json
3. Client stores hashes in audit log
4. Later: Client downloads report and recomputes hashes
5. Compare with stored hashes to verify integrity

**Example**:
```python
import hashlib

# Download report
report_html = requests.get(f"{API_BASE}/reports/{bundle_id}/report.html").text
report_hash = hashlib.sha256(report_html.encode('utf-8')).hexdigest()

# Compare with manifest
manifest = requests.get(f"{API_BASE}/reports/{bundle_id}/manifest").json()
assert report_hash == manifest["hashes"]["report_html_hash"]
```

## Known Limitations

- **No interactivity**: Static HTML (no drill-down, filters, etc.)
- **Basic charts**: Simple SVG (no advanced visualizations like heatmaps)
- **In-memory storage**: Reports lost on server restart (production needs filesystem/S3)
- **No versioning**: Regenerating a report overwrites previous version
- **No compression**: Full HTML in memory (could use gzip)
