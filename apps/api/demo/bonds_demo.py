"""
Demo script showing how to use the bond pricing functions.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.pricing import (
    bond_pv,
    bond_duration,
    bond_convexity,
    bond_dv01
)

def main():
    print("Bond Pricing Demo")
    print("=" * 30)

    # Example parameters
    coupon_rate = 0.05  # 5% annual coupon
    face_value = 1000.0  # Face value of bond
    time_to_maturity = 2.0  # 2 years to maturity
    yield_to_maturity = 0.04  # 4% yield
    payments_per_year = 1  # Annual payments

    # Calculate bond metrics
    pv = bond_pv(coupon_rate, face_value, time_to_maturity, yield_to_maturity, payments_per_year)
    duration = bond_duration(coupon_rate, face_value, time_to_maturity, yield_to_maturity, payments_per_year)
    convexity = bond_convexity(coupon_rate, face_value, time_to_maturity, yield_to_maturity, payments_per_year)
    dv01 = bond_dv01(coupon_rate, face_value, time_to_maturity, yield_to_maturity, payments_per_year)

    print(f"Present Value: ${pv:.2f}")
    print(f"Duration: {duration:.4f} years")
    print(f"Convexity: {convexity:.4f}")
    print(f"DV01: ${dv01:.4f}")
    print()

    # Example with zero coupon
    print("Zero Coupon Bond Example:")
    pv_zero = bond_pv(0.0, face_value, time_to_maturity, yield_to_maturity, payments_per_year)
    print(f"Present Value (Zero Coupon): ${pv_zero:.2f}")

    # Example with zero maturity
    print("Zero Maturity Example:")
    pv_zero_maturity = bond_pv(coupon_rate, face_value, 0.0, yield_to_maturity, payments_per_year)
    print(f"Present Value (Zero Maturity): ${pv_zero_maturity:.2f}")

if __name__ == "__main__":
    main()