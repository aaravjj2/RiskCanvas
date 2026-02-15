#!/usr/bin/env python3
"""
RiskCanvas Demo Pack — runs a deterministic demo and prints results.

Usage:
    python demo/run_demo.py [--json]
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

# Add engine to path
engine_path = str(Path(__file__).resolve().parent.parent / "packages" / "engine")
sys.path.insert(0, engine_path)

from src import (  # noqa: E402
    price_option,
    calculate_greeks,
    portfolio_pnl,
    portfolio_greeks,
    var_parametric,
    var_historical,
    scenario_run,
)


def run_demo() -> dict:
    """Run the full demo suite and return results."""
    results = {}

    # 1. Option pricing
    call_price = price_option(S=100, K=105, T=0.25, r=0.05, sigma=0.2, option_type="call")
    put_price = price_option(S=100, K=105, T=0.25, r=0.05, sigma=0.2, option_type="put")
    results["option_pricing"] = {"call": call_price, "put": put_price}

    # 2. Greeks
    greeks = calculate_greeks(S=100, K=105, T=0.25, r=0.05, sigma=0.2, option_type="call")
    results["greeks"] = greeks

    # 3. Portfolio P&L
    positions = [
        {"symbol": "AAPL", "type": "stock", "quantity": 10, "current_price": 150, "purchase_price": 140},
        {"symbol": "MSFT", "type": "stock", "quantity": 5, "current_price": 380, "purchase_price": 350},
    ]
    pnl = portfolio_pnl(positions)
    results["portfolio_pnl"] = pnl

    # 4. VaR
    var_p = var_parametric(portfolio_value=1_000_000, volatility=0.15, confidence_level=0.95)
    var_h = var_historical(
        current_value=1_000_000,
        historical_returns=[-0.02, 0.01, -0.03, 0.005, -0.015, 0.02, -0.01, 0.008, -0.025, 0.003],
    )
    results["var"] = {"parametric": var_p, "historical": var_h}

    # 5. Scenario analysis
    scenario_results = scenario_run(
        positions=[
            {"type": "stock", "quantity": 10, "current_price": 150, "symbol": "AAPL"},
            {"type": "stock", "quantity": 5, "current_price": 380, "symbol": "MSFT"},
        ],
        scenarios=[
            {"name": "Market Crash -20%", "shock_type": "price", "parameters": {"price_change_pct": -20}},
            {"name": "Rally +10%", "shock_type": "price", "parameters": {"price_change_pct": 10}},
        ],
    )
    results["scenarios"] = scenario_results

    # Overall hash
    results["hash"] = hashlib.sha256(
        json.dumps(results, sort_keys=True, default=str).encode()
    ).hexdigest()

    return results


def main():
    parser = argparse.ArgumentParser(description="RiskCanvas Demo")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    results = run_demo()

    if args.json:
        print(json.dumps(results, indent=2, default=str))
        return

    print("=" * 60)
    print("  RiskCanvas Demo Pack")
    print("=" * 60)
    print()

    print("1. Option Pricing (S=100, K=105, T=0.25, r=5%, vol=20%)")
    print(f"   Call: {results['option_pricing']['call']}")
    print(f"   Put:  {results['option_pricing']['put']}")
    print()

    print("2. Greeks")
    for k, v in results["greeks"].items():
        print(f"   {k:>6}: {v}")
    print()

    print("3. Portfolio P&L")
    print(f"   Total P&L: {results['portfolio_pnl']}")
    print()

    print("4. Value at Risk ($1M portfolio, 15% vol, 95% confidence)")
    print(f"   Parametric: {results['var']['parametric']}")
    print(f"   Historical: {results['var']['historical']}")
    print()

    print("5. Scenario Analysis")
    for s in results["scenarios"]:
        print(f"   {s['name']}: change={s['change']:.2f} ({s['change_pct']:.2f}%)")
    print()

    print(f"Overall Hash: {results['hash']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
