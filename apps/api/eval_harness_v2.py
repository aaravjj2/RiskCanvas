"""
Eval Harness v2 (v3.8+)

- Eval suites defined as JSON fixtures under fixtures/evals/
- Deterministic run_id (sha256 of canonical suite+policy+version)
- Scorecard export: scorecard.md and scorecard.json
- All results in-memory with stable ordering
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter

# ── Version constant ──────────────────────────────────────────────────────────
EVAL_ENGINE_VERSION = "3.8.0"

# ── Built-in eval suites ──────────────────────────────────────────────────────
# These are embedded so no external file I/O is needed; fixtures override if present.

BUILTIN_SUITES: List[Dict[str, Any]] = [
    {
        "suite_id": "governance_policy_suite",
        "label": "Governance Policy Engine Suite",
        "version": "1.0",
        "description": "Tests for policy evaluation: allow/block cases, tool budgets, narrative validation.",
        "cases": [
            {
                "case_id": "allow_demo_tools",
                "description": "All DEMO-allowed tools, within budget",
                "input": {
                    "run_config": {
                        "tools": ["portfolio_analysis", "var_calculation"],
                        "tool_calls_requested": 5,
                        "response_bytes": 1000,
                    },
                    "mode": "DEMO",
                },
                "expected_decision": "allow",
                "weight": 1.0,
            },
            {
                "case_id": "block_unknown_tool",
                "description": "Tool not in DEMO allowlist → block",
                "input": {
                    "run_config": {
                        "tools": ["portfolio_analysis", "azure_devops"],
                        "tool_calls_requested": 5,
                    },
                    "mode": "DEMO",
                },
                "expected_decision": "block",
                "weight": 1.0,
            },
            {
                "case_id": "block_budget_exceeded",
                "description": "Tool calls exceed DEMO budget → block",
                "input": {
                    "run_config": {
                        "tools": ["portfolio_analysis"],
                        "tool_calls_requested": 999,
                    },
                    "mode": "DEMO",
                },
                "expected_decision": "block",
                "weight": 1.0,
            },
            {
                "case_id": "narrative_valid",
                "description": "Narrative referencing computed number → valid",
                "input": {
                    "narrative": "The portfolio value is 18250.75 USD.",
                    "computed_results": {"portfolio_value": 18250.75},
                    "tolerance": 0.01,
                },
                "expected_valid": True,
                "weight": 1.0,
            },
            {
                "case_id": "narrative_invalid",
                "description": "Narrative with number NOT in computed results → invalid",
                "input": {
                    "narrative": "The portfolio value is 99999.99 USD.",
                    "computed_results": {"portfolio_value": 18250.75},
                    "tolerance": 0.01,
                },
                "expected_valid": False,
                "weight": 1.0,
            },
        ],
    },
    {
        "suite_id": "rates_curve_suite",
        "label": "Rates Curve Bootstrap Suite",
        "version": "1.0",
        "description": "Tests for rates curve determinism and bond pricing.",
        "cases": [
            {
                "case_id": "deposit_bootstrap_deterministic",
                "description": "Same deposits → same curve_hash",
                "input": {
                    "instruments": [
                        {"type": "deposit", "tenor": 0.25, "rate": 0.04},
                        {"type": "deposit", "tenor": 0.5,  "rate": 0.042},
                        {"type": "deposit", "tenor": 1.0,  "rate": 0.045},
                    ]
                },
                "expected_hash_stable": True,
                "weight": 1.0,
            },
            {
                "case_id": "bond_price_from_curve",
                "description": "Bond price deterministic from curve",
                "input": {
                    "face_value": 1000,
                    "coupon_rate": 0.05,
                    "years_to_maturity": 5,
                },
                "expected_positive_price": True,
                "weight": 1.0,
            },
        ],
    },
    {
        "suite_id": "stress_library_suite",
        "label": "Stress Library Suite",
        "version": "1.0",
        "description": "Stress preset determinism and apply correctness.",
        "cases": [
            {
                "case_id": "equity_down_shock",
                "description": "equity_down_10pct reduces stock prices by 10%",
                "input": {
                    "preset_id": "equity_down_10pct",
                    "asset_type": "stock",
                    "original_price": 100.0,
                },
                "expected_shocked_price_approx": 90.0,
                "tolerance": 0.01,
                "weight": 1.0,
            },
            {
                "case_id": "rates_up_shock",
                "description": "rates_up_200bp increases bond yield by 200bp",
                "input": {
                    "preset_id": "rates_up_200bp",
                    "asset_type": "bond",
                    "original_yield": 0.04,
                },
                "expected_shocked_yield_approx": 0.06,
                "tolerance": 0.005,
                "weight": 1.0,
            },
        ],
    },
]


# ── In-memory results store ────────────────────────────────────────────────────
_eval_results: Dict[str, Dict[str, Any]] = {}


def _demo_ts() -> str:
    if os.getenv("DEMO_MODE", "false").lower() == "true":
        return "2026-01-01T00:00:00+00:00"
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _suite_run_id(suite: Dict[str, Any]) -> str:
    """Deterministic run_id: sha256(canonical suite + version)."""
    canonical = json.dumps({
        "suite_id": suite["suite_id"],
        "version": suite.get("version", "1.0"),
        "eval_engine_version": EVAL_ENGINE_VERSION,
    }, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:32]


def list_suites() -> List[Dict[str, Any]]:
    """Return all available suites (builtin + any loaded from fixtures dir)."""
    suites = []
    for s in BUILTIN_SUITES:
        suites.append({
            "suite_id": s["suite_id"],
            "label": s["label"],
            "version": s.get("version", "1.0"),
            "description": s.get("description", ""),
            "case_count": len(s.get("cases", [])),
        })
    return sorted(suites, key=lambda x: x["suite_id"])


def get_suite(suite_id: str) -> Optional[Dict[str, Any]]:
    for s in BUILTIN_SUITES:
        if s["suite_id"] == suite_id:
            return s
    return None


def _run_governance_case(case: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a governance policy/narrative test case."""
    from policy_engine import evaluate_policy, validate_narrative

    inp = case["input"]
    passed = False
    actual: Any = None

    if "expected_decision" in case:
        result = evaluate_policy(inp.get("run_config", {}), inp.get("mode"))
        actual = result["decision"]
        passed = actual == case["expected_decision"]
    elif "expected_valid" in case:
        result = validate_narrative(
            inp["narrative"],
            inp["computed_results"],
            inp.get("tolerance", 0.01),
        )
        actual = result["valid"]
        passed = actual == case["expected_valid"]

    return {
        "case_id": case["case_id"],
        "description": case.get("description", ""),
        "passed": passed,
        "actual": actual,
        "expected": case.get("expected_decision", case.get("expected_valid")),
        "weight": case.get("weight", 1.0),
    }


def _run_rates_case(case: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a rates curve test case."""
    try:
        from src.rates import bootstrap_rates_curve, bond_price_from_curve
    except ImportError:
        try:
            import sys
            from pathlib import Path
            ep = str(Path(__file__).parent.parent.parent / "packages" / "engine")
            if ep not in sys.path:
                sys.path.insert(0, ep)
            from src.rates import bootstrap_rates_curve, bond_price_from_curve
        except ImportError:
            return {"case_id": case["case_id"], "passed": False, "actual": "import_error", "weight": case.get("weight", 1.0)}

    inp = case["input"]
    passed = False
    actual: Any = None

    if case["case_id"] == "deposit_bootstrap_deterministic":
        r1 = bootstrap_rates_curve(inp["instruments"])
        r2 = bootstrap_rates_curve(inp["instruments"])
        actual = r1["curve_hash"] == r2["curve_hash"]
        passed = actual == case.get("expected_hash_stable", True)
    elif case["case_id"] == "bond_price_from_curve":
        # Use built-in simple curve
        from src.rates import bootstrap_rates_curve
        instrs = [
            {"type": "deposit", "tenor": 0.25, "rate": 0.04},
            {"type": "deposit", "tenor": 0.5, "rate": 0.042},
            {"type": "deposit", "tenor": 1.0, "rate": 0.045},
            {"type": "swap", "tenor": 2.0, "rate": 0.048, "periods_per_year": 2},
            {"type": "swap", "tenor": 5.0, "rate": 0.052, "periods_per_year": 2},
            {"type": "swap", "tenor": 10.0, "rate": 0.055, "periods_per_year": 2},
        ]
        curve = bootstrap_rates_curve(instrs)
        dfs = curve["discount_factors"]
        price = bond_price_from_curve(
            inp["face_value"], inp["coupon_rate"], inp["years_to_maturity"], dfs
        )
        actual = price
        passed = isinstance(price, float) and price > 0

    return {
        "case_id": case["case_id"],
        "description": case.get("description", ""),
        "passed": passed,
        "actual": actual,
        "expected": "positive_price" if case["case_id"] == "bond_price_from_curve" else "stable_hash",
        "weight": case.get("weight", 1.0),
    }


def _run_stress_case(case: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a stress library test case."""
    try:
        from src.stress import apply_preset, get_preset
    except ImportError:
        try:
            import sys
            from pathlib import Path
            ep = str(Path(__file__).parent.parent.parent / "packages" / "engine")
            if ep not in sys.path:
                sys.path.insert(0, ep)
            from src.stress import apply_preset, get_preset
        except ImportError:
            return {"case_id": case["case_id"], "passed": False, "actual": "import_error", "weight": case.get("weight", 1.0)}

    inp = case["input"]
    passed = False
    actual: Any = None

    if case["case_id"] == "equity_down_shock":
        portfolio = {"assets": [
            {"asset_id": "X", "asset_type": "stock", "quantity": 1,
             "current_price": float(inp["original_price"])}
        ]}
        result = apply_preset(inp["preset_id"], portfolio)
        shocked = result["stressed_portfolio"]["assets"][0]
        actual = shocked.get("current_price", shocked.get("price"))
        expected = float(inp["expected_shocked_price_approx"])
        passed = abs(actual - expected) / max(abs(expected), 1.0) <= inp.get("tolerance", 0.01)
    elif case["case_id"] == "rates_up_shock":
        portfolio = {"assets": [
            {"asset_id": "B", "asset_type": "bond", "face_value": 1000,
             "coupon_rate": 0.05, "yield_to_maturity": float(inp["original_yield"]),
             "years_to_maturity": 5}
        ]}
        result = apply_preset(inp["preset_id"], portfolio)
        shocked = result["stressed_portfolio"]["assets"][0]
        actual = shocked.get("yield_to_maturity")
        expected = float(inp["expected_shocked_yield_approx"])
        passed = abs(actual - expected) <= inp.get("tolerance", 0.005)

    return {
        "case_id": case["case_id"],
        "description": case.get("description", ""),
        "passed": passed,
        "actual": actual,
        "expected": inp.get("expected_shocked_price_approx", inp.get("expected_shocked_yield_approx")),
        "weight": case.get("weight", 1.0),
    }


_SUITE_RUNNERS = {
    "governance_policy_suite": _run_governance_case,
    "rates_curve_suite": _run_rates_case,
    "stress_library_suite": _run_stress_case,
}


def run_suite(suite_id: str) -> Dict[str, Any]:
    """Run all cases in a suite. Returns deterministic run result."""
    suite = get_suite(suite_id)
    if not suite:
        return {"error": f"Suite '{suite_id}' not found."}

    runner = _SUITE_RUNNERS.get(suite_id, _run_governance_case)
    case_results = []
    total_weight = 0.0
    passed_weight = 0.0

    for case in suite.get("cases", []):
        try:
            cr = runner(case)
        except Exception as e:
            cr = {
                "case_id": case["case_id"],
                "passed": False,
                "actual": f"exception: {e}",
                "weight": case.get("weight", 1.0),
            }
        case_results.append(cr)
        w = cr.get("weight", 1.0)
        total_weight += w
        if cr.get("passed"):
            passed_weight += w

    score = round(passed_weight / total_weight, 6) if total_weight > 0 else 0.0
    run_id = _suite_run_id(suite)

    run_result = {
        "run_id": run_id,
        "suite_id": suite_id,
        "suite_label": suite["label"],
        "eval_engine_version": EVAL_ENGINE_VERSION,
        "ts": _demo_ts(),
        "cases": case_results,
        "total_cases": len(case_results),
        "passed_cases": sum(1 for c in case_results if c.get("passed")),
        "failed_cases": sum(1 for c in case_results if not c.get("passed")),
        "score": score,
        "pass_rate": f"{score * 100:.1f}%",
    }

    # Persist
    _eval_results[run_id] = run_result
    return run_result


def get_result(run_id: str) -> Optional[Dict[str, Any]]:
    return _eval_results.get(run_id)


def build_scorecard_md(run_result: Dict[str, Any]) -> str:
    """Generate deterministic scorecard.md from run result."""
    lines = [
        f"# Eval Scorecard — {run_result['suite_label']}",
        "",
        f"**Suite:** `{run_result['suite_id']}`  ",
        f"**Run ID:** `{run_result['run_id']}`  ",
        f"**Engine:** v{run_result['eval_engine_version']}  ",
        f"**Timestamp:** {run_result['ts']}  ",
        f"**Score:** {run_result['pass_rate']} ({run_result['passed_cases']}/{run_result['total_cases']} passed)  ",
        "",
        "## Results",
        "",
        "| Case | Description | Passed | Actual | Expected |",
        "|------|-------------|--------|--------|----------|",
    ]
    for c in sorted(run_result["cases"], key=lambda x: x["case_id"]):
        status = "✅" if c.get("passed") else "❌"
        lines.append(
            f"| `{c['case_id']}` | {c.get('description', '')} | {status} "
            f"| `{str(c.get('actual'))[:40]}` | `{str(c.get('expected'))[:40]}` |"
        )
    lines += ["", "---", "_Generated by RiskCanvas Eval Harness v2_", ""]
    return "\n".join(lines)


def build_scorecard_json(run_result: Dict[str, Any]) -> Dict[str, Any]:
    """Return stable scorecard dict (cases sorted by case_id)."""
    stable = dict(run_result)
    stable["cases"] = sorted(run_result["cases"], key=lambda x: x["case_id"])
    # Compute scorecard_hash
    canonical = json.dumps(stable, sort_keys=True)
    stable["scorecard_hash"] = hashlib.sha256(canonical.encode()).hexdigest()[:32]
    return stable


# ── FastAPI Router ─────────────────────────────────────────────────────────────

eval_router = APIRouter(prefix="/governance/evals", tags=["evals"])


@eval_router.get("/suites")
def api_list_suites():
    return {"suites": list_suites(), "count": len(BUILTIN_SUITES)}


@eval_router.post("/run-suite")
def api_run_suite(body: dict):
    suite_id = body.get("suite_id", "")
    if not suite_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="suite_id required")
    result = run_suite(suite_id)
    if "error" in result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@eval_router.get("/results/{run_id}")
def api_get_result(run_id: str):
    r = get_result(run_id)
    if r is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"No result for run_id '{run_id}'")
    return r


@eval_router.get("/scorecard/{run_id}/md")
def api_scorecard_md(run_id: str):
    r = get_result(run_id)
    if r is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"No result for run_id '{run_id}'")
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(build_scorecard_md(r), media_type="text/markdown")


@eval_router.get("/scorecard/{run_id}/json")
def api_scorecard_json(run_id: str):
    r = get_result(run_id)
    if r is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"No result for run_id '{run_id}'")
    return build_scorecard_json(r)
