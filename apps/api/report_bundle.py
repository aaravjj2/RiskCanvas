"""
Report Bundle Builder for v2.3 - Deterministic self-contained reports with storage

Creates report bundles with:
- Self-contained HTML (no CDN dependencies)
- Embedded SVG charts (deterministic)
- Canonical JSON outputs
- Manifest with hashes
- Storage abstraction (local or Azure Blob)
"""

import json
import hashlib
from typing import Optional, Dict, Any
from pathlib import Path
import os
from storage import IStorage, get_storage_provider


def canonicalize_json(obj: any) -> str:
    """Convert object to canonical JSON"""
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True, default=str)


def generate_report_bundle_id(run_id: str, outputs: Dict[str, Any]) -> str:
    """Generate deterministic report bundle ID from run_id + outputs"""
    outputs_canonical = canonicalize_json(outputs)
    combined = f"{run_id}:{outputs_canonical}"
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()[:32]


def generate_chart_svg(data: Dict[str, Any], chart_type: str) -> str:
    """
    Generate deterministic SVG chart.
    Simple bar/line charts without external dependencies.
    """
    if chart_type == "var_distribution":
        # Simple bar chart showing VaR values
        var_95 = data.get("var_95", 0)
        var_99 = data.get("var_99", 0)
        
        # Normalize to 0-300 pixel height
        max_val = max(abs(var_95), abs(var_99), 1)
        h_95 = abs(var_95) / max_val * 250
        h_99 = abs(var_99) / max_val * 250
        
        svg = f'''<svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
  <rect width="400" height="300" fill="#ffffff"/>
  <text x="200" y="20" text-anchor="middle" font-size="14" font-weight="bold">VaR Distribution</text>
  <rect x="100" y="{300 - h_95 - 30}" width="60" height="{h_95}" fill="#3b82f6"/>
  <text x="130" y="{300 - h_95 - 35}" text-anchor="middle" font-size="12">VaR 95%</text>
  <text x="130" y="{300 - 10}" text-anchor="middle" font-size="12">${var_95 if var_95 else 0:.2f}</text>
  <rect x="240" y="{300 - h_99 - 30}" width="60" height="{h_99}" fill="#ef4444"/>
  <text x="270" y="{300 - h_99 - 35}" text-anchor="middle" font-size="12">VaR 99%</text>
  <text x="270" y="{300 - 10}" text-anchor="middle" font-size="12">${var_99 if var_99 else 0:.2f}</text>
</svg>'''
        return svg
    
    elif chart_type == "greeks":
        # Bar chart for Greeks
        delta = data.get("delta", 0)
        gamma = data.get("gamma", 0)
        vega = data.get("vega", 0)
        theta = data.get("theta", 0)
        
        # Normalize values for display
        values = [abs(delta) * 100, abs(gamma) * 1000, abs(vega) * 10, abs(theta) * 100]
        max_val = max(values + [1])
        
        heights = [v / max_val * 200 for v in values]
        
        svg = f'''<svg width="500" height="300" xmlns="http://www.w3.org/2000/svg">
  <rect width="500" height="300" fill="#ffffff"/>
  <text x="250" y="20" text-anchor="middle" font-size="14" font-weight="bold">Portfolio Greeks</text>
  <rect x="50" y="{280 - heights[0]}" width="80" height="{heights[0]}" fill="#3b82f6"/>
  <text x="90" y="295" text-anchor="middle" font-size="11">Delta</text>
  <rect x="150" y="{280 - heights[1]}" width="80" height="{heights[1]}" fill="#10b981"/>
  <text x="190" y="295" text-anchor="middle" font-size="11">Gamma</text>
  <rect x="250" y="{280 - heights[2]}" width="80" height="{heights[2]}" fill="#f59e0b"/>
  <text x="290" y="295" text-anchor="middle" font-size="11">Vega</text>
  <rect x="350" y="{280 - heights[3]}" width="80" height="{heights[3]}" fill="#ef4444"/>
  <text x="390" y="295" text-anchor="middle" font-size="11">Theta</text>
</svg>'''
        return svg
    
    return '<svg width="400" height="300"><text x="200" y="150">Chart not available</text></svg>'


def build_report_html(run_data: Dict[str, Any], portfolio_data: Dict[str, Any]) -> str:
    """
    Build self-contained HTML report (no CDN dependencies).
    All styles inline, charts embedded as SVG.
    """
    outputs = run_data.get("outputs", {})
    pricing = outputs.get("pricing", {})
    greeks = outputs.get("greeks", {})
    var = outputs.get("var", {})
    
    portfolio_value = pricing.get("portfolio_value", 0)
    total_pnl = pricing.get("total_pnl", 0)
    var_95 = var.get("var_95", 0)
    var_99 = var.get("var_99", 0)
    
    # Generate charts
    var_chart = generate_chart_svg(var, "var_distribution")
    greeks_chart = generate_chart_svg(greeks, "greeks") if greeks else ""
    
    # Greeks section HTML
    greeks_section = ""
    if greeks:
        greeks_section = f'''<h2>Portfolio Greeks</h2>
        <div class="chart">
            {greeks_chart}
        </div>'''
    
    # Portfolio positions table
    positions_html = ""
    for asset in portfolio_data.get("assets", []):
        symbol = asset.get("symbol", "N/A")
        asset_type = asset.get("type", "stock")
        quantity = asset.get("quantity", 0)
        price = asset.get("current_price", asset.get("price", 0))
        value = quantity * price
        
        positions_html += f'''
        <tr>
            <td>{symbol}</td>
            <td>{asset_type}</td>
            <td>{quantity}</td>
            <td>${price:.2f}</td>
            <td>${value:.2f}</td>
        </tr>'''
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RiskCanvas Report - {run_data.get("run_id", "N/A")[:8]}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            background: #f9fafb;
            padding: 2rem;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        h1 {{ color: #111827; margin-bottom: 0.5rem; }}
        h2 {{ color: #374151; margin-top: 2rem; margin-bottom: 1rem; border-bottom: 2px solid #e5e7eb; padding-bottom: 0.5rem; }}
        .meta {{ color: #6b7280; font-size: 0.875rem; margin-bottom: 2rem; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
        .metric-card {{
            background: #f3f4f6;
            padding: 1.5rem;
            border-radius: 6px;
            border-left: 4px solid #3b82f6;
        }}
        .metric-label {{ font-size: 0.875rem; color: #6b7280; margin-bottom: 0.5rem; }}
        .metric-value {{ font-size: 1.5rem; font-weight: 700; color: #111827; }}
        .chart {{ margin: 2rem 0; text-align: center; }}
        table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
        th, td {{ padding: 0.75rem; text-align: left; border-bottom: 1px solid #e5e7eb; }}
        th {{ background: #f9fafb; font-weight: 600; color: #374151; }}
        .footer {{ margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 0.875rem; text-align: center; }}
        .hash {{ font-family: monospace; font-size: 0.75rem; color: #9ca3af; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>RiskCanvas Risk Analytics Report</h1>
        <div class="meta">
            <div>Run ID: <span class="hash">{run_data.get("run_id", "N/A")}</span></div>
            <div>Portfolio ID: <span class="hash">{run_data.get("portfolio_id", "N/A")}</span></div>
            <div>Engine Version: {run_data.get("engine_version", "N/A")}</div>
            <div>Generated: {run_data.get("created_at", "N/A")}</div>
        </div>
        
        <h2>Key Metrics</h2>
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-label">Portfolio Value</div>
                <div class="metric-value">${portfolio_value:,.2f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total P&L</div>
                <div class="metric-value">${total_pnl:,.2f}</div>
            </div>
            <div class="metric-card" style="border-left-color: #ef4444;">
                <div class="metric-label">VaR (95%)</div>
                <div class="metric-value">${var_95:,.2f}</div>
            </div>
            <div class="metric-card" style="border-left-color: #dc2626;">
                <div class="metric-label">VaR (99%)</div>
                <div class="metric-value">${var_99:,.2f}</div>
            </div>
        </div>
        
        <h2>Risk Distribution</h2>
        <div class="chart">
            {var_chart}
        </div>
        
        {greeks_section}
        
        <h2>Portfolio Positions</h2>
        <table>
            <thead>
                <tr>
                    <th>Symbol</th>
                    <th>Type</th>
                    <th>Quantity</th>
                    <th>Price</th>
                    <th>Market Value</th>
                </tr>
            </thead>
            <tbody>
                {positions_html}
            </tbody>
        </table>
        
        <div class="footer">
            <div>RiskCanvas v1.3.0 - Deterministic Risk Analytics Platform</div>
            <div class="hash">Output Hash: {run_data.get("output_hash", "N/A")}</div>
        </div>
    </div>
</body>
</html>'''
    
    return html


def build_report_manifest(run_data: Dict[str, Any], report_bundle_id: str, storage_info: Dict[str, Any] = None) -> Dict[str, Any]:
    """Build report manifest with all hashes, metadata, and storage info"""
    outputs = run_data.get("outputs", {})
    
    manifest = {
        "report_bundle_id": report_bundle_id,
        "run_id": run_data.get("run_id"),
        "portfolio_id": run_data.get("portfolio_id"),
        "engine_version": run_data.get("engine_version"),
        "created_at": run_data.get("created_at"),
        "hashes": {
            "output_hash": run_data.get("output_hash"),
            "report_html_hash": hashlib.sha256(
                build_report_html(run_data, {}).encode('utf-8')
            ).hexdigest(),
            "run_json_hash": hashlib.sha256(
                canonicalize_json(outputs).encode('utf-8')
            ).hexdigest()
        },
        "storage": storage_info or {},
        "files": {
            "report.html": f"reports/{report_bundle_id}/report.html",
            "run.json": f"reports/{report_bundle_id}/run.json",
            "manifest.json": f"reports/{report_bundle_id}/manifest.json"
        }
    }
    
    return manifest


def store_report_bundle_to_storage(
    report_bundle_id: str,
    run_data: Dict[str, Any],
    portfolio_data: Dict[str, Any],
    storage: Optional[IStorage] = None
) -> Dict[str, Any]:
    """
    Store report bundle using storage provider.
    Returns manifest with storage info and download URLs.
    """
    if storage is None:
        storage = get_storage_provider()
    
    # Build artifacts
    report_html = build_report_html(run_data, portfolio_data)
    run_json = canonicalize_json(run_data["outputs"])
    
    # Store files
    html_key = f"reports/{report_bundle_id}/report.html"
    json_key = f"reports/{report_bundle_id}/run.json"
    manifest_key = f"reports/{report_bundle_id}/manifest.json"
    
    # Store HTML
    html_result = storage.store(html_key, report_html.encode('utf-8'), "text/html")
    
    # Store JSON
    json_result = storage.store(json_key, run_json.encode('utf-8'), "application/json")
    
    # Build manifest with storage info
    storage_info = {
        "provider": html_result.get("provider", "unknown"),
        "stored_at": html_result.get("stored_at"),
        "files": {
            "report.html": {
                "sha256": html_result.get("sha256"),
                "size": len(report_html.encode('utf-8'))
            },
            "run.json": {
                "sha256": json_result.get("sha256"),
                "size": len(run_json.encode('utf-8'))
            }
        }
    }
    
    manifest = build_report_manifest(run_data, report_bundle_id, storage_info)
    manifest_json = canonicalize_json(manifest)
    
    # Store manifest
    manifest_result = storage.store(manifest_key, manifest_json.encode('utf-8'), "application/json")
    
    # Add manifest hash
    manifest["hashes"]["manifest_hash"] = manifest_result.get("sha256")
    
    return manifest


def get_report_bundle_from_storage(
    report_bundle_id: str,
    storage: Optional[IStorage] = None
) -> Optional[Dict[str, Any]]:
    """Retrieve report bundle from storage."""
    if storage is None:
        storage = get_storage_provider()
    
    manifest_key = f"reports/{report_bundle_id}/manifest.json"
    
    try:
        if not storage.exists(manifest_key):
            return None
        
        manifest_bytes = storage.retrieve(manifest_key)
        manifest = json.loads(manifest_bytes.decode('utf-8'))
        return manifest
    except Exception:
        return None


def get_download_urls(
    report_bundle_id: str,
    expires_in: int = 3600,
    storage: Optional[IStorage] = None
) -> Dict[str, str]:
    """Get signed/proxy download URLs for all files in report bundle."""
    if storage is None:
        storage = get_storage_provider()
    
    files = ["report.html", "run.json", "manifest.json"]
    urls = {}
    
    for filename in files:
        key = f"reports/{report_bundle_id}/{filename}"
        if storage.exists(key):
            urls[filename] = storage.get_download_url(key, expires_in)
    
    return urls


# Legacy in-memory storage (for backwards compatibility during migration)
_report_bundles: Dict[str, Dict[str, Any]] = {}


def store_report_bundle(report_bundle_id: str, bundle_data: Dict[str, Any]):
    """Store report bundle in memory"""
    _report_bundles[report_bundle_id] = bundle_data


def get_report_bundle(report_bundle_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve report bundle"""
    return _report_bundles.get(report_bundle_id)


def clear_report_bundles():
    """Clear all report bundles (for testing)"""
    global _report_bundles
    _report_bundles = {}
