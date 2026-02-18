"""
Rates Curve Module — Deterministic Bootstrap (v3.4+)

Supports a simplified curve bootstrap from deposit + swap instruments.
Output: zero curve (tenor → zero rate) + discount factors, ordered by tenor ascending.

Design:
  - Deterministic: fixed iteration count, fixed rounding (6 decimal places)
  - No external dependencies
  - Canonical output: sorted by tenor ascending
"""

import math
from typing import Dict, List, Any, Optional


# ── Constants ─────────────────────────────────────────────────────────────────

_ROUNDING = 6   # decimal places for all output values


def _r(v: float) -> float:
    return round(v, _ROUNDING)


# ── Bootstrap ─────────────────────────────────────────────────────────────────

def bootstrap_rates_curve(instruments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Deterministic bootstrap of a zero curve from a list of instruments.

    Each instrument is a dict with:
      - type    : "deposit" | "swap"
      - tenor   : float (years, e.g. 0.25, 0.5, 1.0, 2.0, 5.0, 10.0)
      - rate    : float (e.g. 0.04 = 4%)
      - (optional) periods_per_year : int, default 1 for deposits, 1 for swaps

    Returns dict with:
      - instruments : input (pass-through)
      - zero_rates  : [{tenor, zero_rate}] sorted ascending by tenor
      - discount_factors : [{tenor, df}] sorted ascending by tenor
      - curve_hash : sha256 of canonical output
    """
    if not instruments:
        raise ValueError("instruments list must not be empty")

    # Sort instruments by tenor ascending (deterministic ordering)
    sorted_instr = sorted(instruments, key=lambda x: float(x["tenor"]))

    zero_rates: Dict[float, float] = {}
    discount_factors: Dict[float, float] = {}

    for instr in sorted_instr:
        tenor = float(instr["tenor"])
        rate = float(instr["rate"])
        instr_type = str(instr.get("type", "deposit")).lower()

        if instr_type == "deposit":
            # Simple deposit: zero rate ≈ par rate (Act/365 simple)
            zero_rate = _r(rate)
            df = _r(1.0 / (1.0 + rate * tenor))

        elif instr_type == "swap":
            # Fixed swap coupon bootstrapped from known shorter-tenor DFs
            # Coupon periods: semi-annual by default
            periods_per_year = int(instr.get("periods_per_year", 2))
            dt = 1.0 / periods_per_year
            n_periods = max(1, round(tenor * periods_per_year))
            coupon = rate / periods_per_year

            # Sum PV of known coupon payments
            pv_known = 0.0
            for i in range(1, n_periods):
                t_i = _r(i * dt)
                # Interpolate DF for t_i
                df_i = _interpolate_df(t_i, discount_factors)
                pv_known += coupon * df_i

            # Bootstrap final discount factor
            # 1 = coupon * df_T + (1 + coupon) * df_final → solve for df_final
            denom = 1.0 + coupon
            if abs(denom) < 1e-12:
                raise ValueError(f"Degenerate swap at tenor {tenor}")
            df_final = _r((1.0 - pv_known) / denom)
            df_final = max(1e-8, df_final)  # floor to avoid log(0)

            # Implied zero rate from discount factor
            zero_rate = _r(-math.log(df_final) / tenor) if tenor > 0 else 0.0
            df = df_final

        else:
            raise ValueError(f"Unknown instrument type: {instr_type!r}")

        zero_rates[tenor] = zero_rate
        discount_factors[tenor] = df

    # Build sorted output lists
    tenors_sorted = sorted(zero_rates.keys())
    zero_curve = [{"tenor": t, "zero_rate": zero_rates[t]} for t in tenors_sorted]
    df_curve = [{"tenor": t, "df": discount_factors[t]} for t in tenors_sorted]

    # Canonical hash for determinism verification
    import hashlib, json
    canonical = json.dumps({
        "zero_rates": zero_curve,
        "discount_factors": df_curve,
    }, sort_keys=True, separators=(",", ":"))
    curve_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    return {
        "instruments": sorted_instr,
        "zero_rates": zero_curve,
        "discount_factors": df_curve,
        "curve_hash": curve_hash,
    }


def _interpolate_df(tenor: float, discount_factors: Dict[float, float]) -> float:
    """
    Linear interpolation of discount factor.
    If tenor < all known tenors: flat extrapolation from shortest.
    If tenor > all known tenors: flat extrapolation from longest.
    """
    if not discount_factors:
        # No known DFs yet — flat at 1.0
        return 1.0

    tenors = sorted(discount_factors.keys())

    if tenor <= tenors[0]:
        return discount_factors[tenors[0]]
    if tenor >= tenors[-1]:
        return discount_factors[tenors[-1]]

    # Find bracketing tenors
    for i in range(len(tenors) - 1):
        t_lo = tenors[i]
        t_hi = tenors[i + 1]
        if t_lo <= tenor <= t_hi:
            df_lo = discount_factors[t_lo]
            df_hi = discount_factors[t_hi]
            alpha = (tenor - t_lo) / (t_hi - t_lo)
            return _r(df_lo + alpha * (df_hi - df_lo))

    return discount_factors[tenors[-1]]


def bond_price_from_curve(
    face_value: float,
    coupon_rate: float,
    years_to_maturity: float,
    discount_factors: List[Dict[str, Any]],
    periods_per_year: int = 2,
) -> float:
    """
    Price a bond using a discount factor curve instead of a flat yield.

    Coupon payment at each period is discounted by the interpolated DF at that tenor.
    Face value is discounted by DF at maturity.
    """
    if years_to_maturity <= 0:
        return round(face_value, _ROUNDING)

    # Build a dict from the curve list
    df_map: Dict[float, float] = {}
    for item in discount_factors:
        df_map[float(item["tenor"])] = float(item["df"])

    dt = 1.0 / periods_per_year
    n_periods = max(1, round(years_to_maturity * periods_per_year))
    coupon_payment = face_value * coupon_rate / periods_per_year

    price = 0.0
    for t_idx in range(1, n_periods + 1):
        t = _r(t_idx * dt)
        df = _interpolate_df(t, df_map)
        price += coupon_payment * df

    # Add PV of face value
    df_mat = _interpolate_df(_r(years_to_maturity), df_map)
    price += face_value * df_mat

    return round(price, _ROUNDING)
