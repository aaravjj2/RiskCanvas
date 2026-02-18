"""
Stress Library Module — Deterministic Scenario Presets (v3.5+)

Provides canonical stress scenario definitions (presets).
Each preset is a typed, immutable payload with a stable hash.

Presets:
  - rates_up_200bp
  - rates_down_200bp
  - vol_up_25pct
  - equity_down_10pct
  - credit_spread_up_100bp
"""

import hashlib
import json
from typing import Any, Dict, List, Optional


# ── Canonical helper ──────────────────────────────────────────────────────────

def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ── Preset definitions ────────────────────────────────────────────────────────

_PRESETS: Dict[str, Dict[str, Any]] = {
    "rates_up_200bp": {
        "preset_id": "rates_up_200bp",
        "label": "Rates +200 bp",
        "description": "Parallel shift: all interest rates up by 200 basis points.",
        "shocks": {
            "interest_rate_shift_bp": 200,
            "volatility_shift_pct": 0.0,
            "equity_shift_pct": 0.0,
            "credit_spread_shift_bp": 0,
        },
        "category": "rates",
    },
    "rates_down_200bp": {
        "preset_id": "rates_down_200bp",
        "label": "Rates -200 bp",
        "description": "Parallel shift: all interest rates down by 200 basis points.",
        "shocks": {
            "interest_rate_shift_bp": -200,
            "volatility_shift_pct": 0.0,
            "equity_shift_pct": 0.0,
            "credit_spread_shift_bp": 0,
        },
        "category": "rates",
    },
    "vol_up_25pct": {
        "preset_id": "vol_up_25pct",
        "label": "Volatility +25%",
        "description": "Implied volatility of all options increases by 25%.",
        "shocks": {
            "interest_rate_shift_bp": 0,
            "volatility_shift_pct": 0.25,
            "equity_shift_pct": 0.0,
            "credit_spread_shift_bp": 0,
        },
        "category": "volatility",
    },
    "equity_down_10pct": {
        "preset_id": "equity_down_10pct",
        "label": "Equity -10%",
        "description": "All equity prices fall by 10%.",
        "shocks": {
            "interest_rate_shift_bp": 0,
            "volatility_shift_pct": 0.0,
            "equity_shift_pct": -0.10,
            "credit_spread_shift_bp": 0,
        },
        "category": "equity",
    },
    "credit_spread_up_100bp": {
        "preset_id": "credit_spread_up_100bp",
        "label": "Credit Spread +100 bp",
        "description": "All credit spreads widen by 100 basis points.",
        "shocks": {
            "interest_rate_shift_bp": 0,
            "volatility_shift_pct": 0.0,
            "equity_shift_pct": 0.0,
            "credit_spread_shift_bp": 100,
        },
        "category": "credit",
    },
}


def list_presets() -> List[Dict[str, Any]]:
    """Return all presets with their stable hashes, sorted by preset_id."""
    result = []
    for preset_id in sorted(_PRESETS.keys()):
        p = dict(_PRESETS[preset_id])
        p["preset_hash"] = _sha256(_canonical(p))
        result.append(p)
    return result


def get_preset(preset_id: str) -> Optional[Dict[str, Any]]:
    """Get a single preset by ID (with hash)."""
    p = _PRESETS.get(preset_id)
    if p is None:
        return None
    result = dict(p)
    result["preset_hash"] = _sha256(_canonical(p))
    return result


def apply_preset(
    preset_id: str,
    portfolio: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Apply a stress preset to a portfolio input dict.

    Returns a stressed portfolio dict with:
      - assets with shocked prices/vols
      - stress_preset_id
      - input_hash (hash of original portfolio)
      - stressed_input_hash (hash of stressed portfolio)
    """
    preset = get_preset(preset_id)
    if preset is None:
        raise ValueError(f"Unknown preset: {preset_id!r}")

    shocks = preset["shocks"]
    equity_shift = shocks.get("equity_shift_pct", 0.0)
    vol_shift = shocks.get("volatility_shift_pct", 0.0)
    rate_shift_bp = shocks.get("interest_rate_shift_bp", 0)

    original_input_hash = _sha256(_canonical(portfolio))
    assets = portfolio.get("assets", [])

    stressed_assets = []
    for asset in assets:
        a = dict(asset)
        asset_type = str(a.get("type", "stock")).lower()

        if asset_type in ("stock", "equity"):
            if equity_shift != 0.0:
                for price_field in ("price", "current_price"):
                    if price_field in a and a[price_field] is not None:
                        a[price_field] = round(float(a[price_field]) * (1 + equity_shift), 6)

        elif asset_type == "option":
            if vol_shift != 0.0 and "volatility" in a:
                a["volatility"] = round(float(a["volatility"]) * (1 + vol_shift), 6)
            # Equity shock still applies to underlying
            if equity_shift != 0.0:
                for price_field in ("price", "current_price", "spot_price"):
                    if price_field in a and a[price_field] is not None:
                        a[price_field] = round(float(a[price_field]) * (1 + equity_shift), 6)

        elif asset_type == "bond":
            if rate_shift_bp != 0:
                shift_decimal = rate_shift_bp / 10000.0
                for ytm_field in ("yield_to_maturity", "ytm", "rate"):
                    if ytm_field in a and a[ytm_field] is not None:
                        a[ytm_field] = round(float(a[ytm_field]) + shift_decimal, 6)

        stressed_assets.append(a)

    stressed_portfolio = dict(portfolio)
    stressed_portfolio["assets"] = stressed_assets
    stressed_portfolio["stress_preset_id"] = preset_id

    stressed_input_hash = _sha256(_canonical(stressed_portfolio))

    return {
        "stressed_portfolio": stressed_portfolio,
        "stress_preset_id": preset_id,
        "preset_label": preset["label"],
        "input_hash": original_input_hash,
        "stressed_input_hash": stressed_input_hash,
        "shocks_applied": shocks,
    }
