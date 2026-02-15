"""
Comprehensive test suite for RiskCanvas API (v0.2)
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add API to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app

client = TestClient(app)


# ===== Health and Version Tests =====


def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_version_endpoint():
    """Test version endpoint"""
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert "api_version" in data
    assert "engine_version" in data


# ===== Option Pricing Tests =====


def test_price_option_call():
    """Test pricing a call option"""
    request = {
        "S": 100.0,
        "K": 105.0,
        "T": 0.25,
        "r": 0.05,
        "sigma": 0.2,
        "option_type": "call"
    }
    
    response = client.post("/price/option", json=request)
    assert response.status_code == 200
    data = response.json()
    
    assert "request_id" in data
    assert "price" in data
    assert data["price"] > 0
    assert "greeks" in data
    assert "delta" in data["greeks"]


def test_price_option_put():
    """Test pricing a put option"""
    request = {
        "S": 100.0,
        "K": 95.0,
        "T": 0.5,
        "r": 0.05,
        "sigma": 0.25,
        "option_type": "put"
    }
    
    response = client.post("/price/option", json=request)
    assert response.status_code == 200
    data = response.json()
    
    assert "price" in data
    assert data["price"] > 0


def test_price_option_at_expiration():
    """Test option pricing at expiration (T=0)"""
    request = {
        "S": 110.0,
        "K": 100.0,
        "T": 0.0,
        "r": 0.05,
        "sigma": 0.2,
        "option_type": "call"
    }
    
    response = client.post("/price/option", json=request)
    assert response.status_code == 200
    data = response.json()
    
    # At expiration, call should be worth intrinsic value: S - K = 10
    assert data["price"] == 10.0
    assert any("expiration" in w.lower() for w in data["warnings"])


# ===== Portfolio Analysis Tests =====


def test_analyze_portfolio_basic():
    """Test basic portfolio analysis"""
    request = {
        "portfolio": {
            "id": "test-001",
            "name": "Test Portfolio",
            "assets": [
                {
                    "symbol": "AAPL",
                    "type": "stock",
                    "quantity": 10,
                    "price": 150.0,
                    "current_price": 150.0,
                    "purchase_price": 140.0
                },
                {
                    "symbol": "MSFT",
                    "type": "stock",
                    "quantity": 5,
                    "price": 300.0,
                    "current_price": 300.0,
                    "purchase_price": 290.0
                }
            ]
        }
    }
    
    response = client.post("/analyze/portfolio", json=request)
    assert response.status_code == 200
    data = response.json()
    
    assert "request_id" in data
    assert "metrics" in data
    assert data["metrics"]["total_pnl"] == 150.0  # (150-140)*10 + (300-290)*5
    assert data["metrics"]["total_value"] == 3000.0  # 150*10 + 300*5
    assert data["metrics"]["asset_count"] == 2


def test_analyze_portfolio_with_options():
    """Test portfolio analysis with options"""
    request = {
        "portfolio": {
            "id": "test-002",
            "name": "Options Portfolio",
            "assets": [
                {
                    "symbol": "AAPL-CALL",
                    "type": "option",
                    "quantity": 1,
                    "S": 150.0,
                    "K": 155.0,
                    "T": 0.25,
                    "r": 0.05,
                    "sigma": 0.3,
                    "option_type": "call",
                    "current_price": 5.0,
                    "purchase_price": 4.0
                }
            ]
        }
    }
    
    response = client.post("/analyze/portfolio", json=request)
    assert response.status_code == 200
    data = response.json()
    
    assert "metrics" in data
    assert data["metrics"]["portfolio_greeks"] is not None
    assert "delta" in data["metrics"]["portfolio_greeks"]


# ===== VaR Tests =====


def test_var_parametric():
    """Test parametric VaR calculation"""
    request = {
        "portfolio_value": 1000000.0,
        "method": "parametric",
        "volatility": 0.15,
        "confidence_level": 0.95,
        "time_horizon_days": 1
    }
    
    response = client.post("/risk/var", json=request)
    assert response.status_code == 200
    data = response.json()
    
    assert "request_id" in data
    assert "var_value" in data
    assert data["var_value"] > 0
    assert data["method"] == "parametric"
    assert data["confidence_level"] == 0.95


def test_var_historical():
    """Test historical VaR calculation"""
    request = {
        "portfolio_value": 1000000.0,
        "method": "historical",
        "historical_returns": [-0.05, -0.02, -0.01, 0.01, 0.02, 0.03, 0.04, 0.05],
        "confidence_level": 0.95
    }
    
    response = client.post("/risk/var", json=request)
    assert response.status_code == 200
    data = response.json()
    
    assert "var_value" in data
    assert data["method"] == "historical"


def test_var_missing_volatility():
    """Test VaR with missing required parameter"""
    request = {
        "portfolio_value": 1000000.0,
        "method": "parametric",
        # Missing volatility
        "confidence_level": 0.95
    }
    
    response = client.post("/risk/var", json=request)
    assert response.status_code == 400


# ===== Scenario Tests =====


def test_scenario_run_price_shock():
    """Test scenario analysis with price shock"""
    request = {
        "positions": [
            {
                "symbol": "AAPL",
                "type": "stock",
                "quantity": 100,
                "current_price": 150.0,
                "purchase_price": 140.0
            }
        ],
        "scenarios": [
            {
                "name": "Market Crash -20%",
                "shock_type": "price",
                "parameters": {"price_change_pct": -20.0}
            },
            {
                "name": "Market Rally +10%",
                "shock_type": "price",
                "parameters": {"price_change_pct": 10.0}
            }
        ]
    }
    
    response = client.post("/scenario/run", json=request)
    assert response.status_code == 200
    data = response.json()
    
    assert "scenarios" in data
    assert len(data["scenarios"]) == 2
    
    crash_scenario = data["scenarios"][0]
    assert crash_scenario["name"] == "Market Crash -20%"
    assert crash_scenario["change"] < 0  # Portfolio value should decrease
    
    rally_scenario = data["scenarios"][1]
    assert rally_scenario["name"] == "Market Rally +10%"
    assert rally_scenario["change"] > 0  # Portfolio value should increase


def test_scenario_run_combined_shock():
    """Test scenario with combined shocks"""
    request = {
        "positions": [
            {
                "symbol": "AAPL-CALL",
                "type": "option",
                "quantity": 1,
                "S": 150.0,
                "K": 155.0,
                "T": 0.25,
                "r": 0.05,
                "sigma": 0.3,
                "option_type": "call"
            }
        ],
        "scenarios": [
            {
                "name": "Combined Stress",
                "shock_type": "combined",
                "parameters": {
                    "price_change_pct": -10.0,
                    "volatility_change_pct": 50.0,
                    "rate_change_bps": 100
                }
            }
        ]
    }
    
    response = client.post("/scenario/run", json=request)
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["scenarios"]) == 1


# ===== Report Generation Tests =====


def test_generate_report():
    """Test report generation"""
    request = {
        "portfolio": {
            "id": "test-003",
            "name": "Report Test Portfolio",
            "assets": [
                {
                    "symbol": "AAPL",
                    "type": "stock",
                    "quantity": 10,
                    "price": 150.0,
                    "current_price": 150.0,
                    "purchase_price": 140.0
                }
            ]
        },
        "include_greeks": True,
        "include_var": True
    }
    
    response = client.post("/report/generate", json=request)
    assert response.status_code == 200
    data = response.json()
    
    assert "request_id" in data
    assert "html" in data
    assert data["html"] is not None
    assert "<!DOCTYPE html>" in data["html"]
    assert data["metrics"]["total_pnl"] == 100.0
    assert data["var"] is not None


# ===== Determinism Tests =====


def test_determinism_option_pricing():
    """Test that option pricing is deterministic"""
    request = {
        "S": 100.0,
        "K": 105.0,
        "T": 0.25,
        "r": 0.05,
        "sigma": 0.2,
        "option_type": "call"
    }
    
    # Call multiple times
    responses = [client.post("/price/option", json=request) for _ in range(5)]
    
    # All should succeed
    assert all(r.status_code == 200 for r in responses)
    
    # Extract prices
    prices = [r.json()["price"] for r in responses]
    
    # All prices should be identical
    assert len(set(prices)) == 1


def test_determinism_portfolio_analysis():
    """Test that portfolio analysis is deterministic"""
    request = {
        "portfolio": {
            "assets": [
                {
                    "symbol": "AAPL",
                    "type": "stock",
                    "quantity": 10,
                    "price": 150.0,
                    "current_price": 150.0,
                    "purchase_price": 140.0
                }
            ]
        }
    }
    
    # Call multiple times
    responses = [client.post("/analyze/portfolio", json=request) for _ in range(5)]
    
    # All should succeed
    assert all(r.status_code == 200 for r in responses)
    
    # Extract P&L values
    pnl_values = [r.json()["metrics"]["total_pnl"] for r in responses]
    
    # All should be identical
    assert len(set(pnl_values)) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
