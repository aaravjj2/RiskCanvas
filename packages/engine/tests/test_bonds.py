"""
Tests for Bond Analytics Module
"""

import pytest
from src.bonds import (
    bond_price_from_yield,
    bond_yield_from_price,
    bond_duration,
    bond_convexity,
    bond_risk_metrics
)


def test_bond_price_at_par():
    """Test bond price when yield equals coupon rate (should be par)"""
    price = bond_price_from_yield(
        face_value=1000.0,
        coupon_rate=0.05,
        years_to_maturity=5.0,
        yield_to_maturity=0.05,
        periods_per_year=2
    )
    assert abs(price - 1000.0) < 0.1


def test_bond_price_discount():
    """Test bond price when yield > coupon (discount bond)"""
    price = bond_price_from_yield(
        face_value=1000.0,
        coupon_rate=0.04,
        years_to_maturity=5.0,
        yield_to_maturity=0.06,
        periods_per_year=2
    )
    assert price < 1000.0
    assert abs(price - 914.7) < 5.0  # Approximate check


def test_bond_price_premium():
    """Test bond price when yield < coupon (premium bond)"""
    price = bond_price_from_yield(
        face_value=1000.0,
        coupon_rate=0.06,
        years_to_maturity=5.0,
        yield_to_maturity=0.04,
        periods_per_year=2
    )
    assert price > 1000.0
    assert abs(price - 1089.8) < 5.0  # Approximate check


def test_bond_price_zero_maturity():
    """Test bond price at maturity returns face value"""
    price = bond_price_from_yield(
        face_value=1000.0,
        coupon_rate=0.05,
        years_to_maturity=0.0,
        yield_to_maturity=0.05
    )
    assert price == 1000.0


def test_bond_yield_from_price_at_par():
    """Test yield calculation when price equals par"""
    ytm = bond_yield_from_price(
        face_value=1000.0,
        coupon_rate=0.05,
        years_to_maturity=5.0,
        price=1000.0,
        periods_per_year=2
    )
    assert abs(ytm - 0.05) < 0.001


def test_bond_yield_from_price_discount():
    """Test yield calculation for discount bond"""
    # First calculate price for known yield
    known_yield = 0.06
    price = bond_price_from_yield(1000.0, 0.04, 5.0, known_yield, 2)
    
    # Then recover yield from price
    calculated_yield = bond_yield_from_price(1000.0, 0.04, 5.0, price, 2)
    
    assert abs(calculated_yield - known_yield) < 0.001


def test_bond_duration():
    """Test Macaulay duration calculation"""
    duration = bond_duration(
        face_value=1000.0,
        coupon_rate=0.05,
        years_to_maturity=5.0,
        yield_to_maturity=0.05,
        periods_per_year=2
    )
    # For a 5-year bond at par, duration should be less than 5 years
    assert 4.0 < duration < 5.0


def test_bond_duration_zero_coupon():
    """Test duration of zero-coupon bond equals maturity"""
    duration = bond_duration(
        face_value=1000.0,
        coupon_rate=0.0,
        years_to_maturity=10.0,
        yield_to_maturity=0.05,
        periods_per_year=1
    )
    # Zero-coupon bond duration equals maturity
    assert abs(duration - 10.0) < 0.1


def test_bond_convexity():
    """Test convexity calculation"""
    convexity = bond_convexity(
        face_value=1000.0,
        coupon_rate=0.05,
        years_to_maturity=5.0,
        yield_to_maturity=0.05,
        periods_per_year=2
    )
    # Convexity should be positive
    assert convexity > 0
    # For a 5-year bond, convexity typically in range 20-40
    assert 15.0 < convexity < 50.0


def test_bond_risk_metrics():
    """Test comprehensive risk metrics"""
    metrics = bond_risk_metrics(
        face_value=1000.0,
        coupon_rate=0.05,
        years_to_maturity=5.0,
        yield_to_maturity=0.05,
        periods_per_year=2
    )
    
    assert "price" in metrics
    assert "duration" in metrics
    assert "modified_duration" in metrics
    assert "convexity" in metrics
    
    # At par
    assert abs(metrics["price"] - 1000.0) < 0.1
    # Duration < maturity
    assert 4.0 < metrics["duration"] < 5.0
    # Modified duration < duration
    assert metrics["modified_duration"] < metrics["duration"]
    # Convexity > 0
    assert metrics["convexity"] > 0


def test_bond_determinism():
    """Test that same inputs produce same outputs"""
    metrics1 = bond_risk_metrics(1000.0, 0.06, 10.0, 0.05, 2)
    metrics2 = bond_risk_metrics(1000.0, 0.06, 10.0, 0.05, 2)
    
    assert metrics1 == metrics2
