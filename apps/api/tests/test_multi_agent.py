"""
Test suite for multi-agent system
"""

import pytest
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.multi_agent import (
    IntakeAgent,
    RiskAgent,
    ReportAgent,
    MultiAgentCoordinator,
    Position,
    NormalizedPortfolio,
    RiskMetrics,
    AgentStatus
)
from llm.providers import MockProvider


@pytest.fixture
def sample_raw_portfolio():
    """Sample raw portfolio"""
    return {
        "id": "test-001",
        "name": "Test Portfolio",
        "assets": [
            {
                "symbol": "AAPL",
                "type": "stock",
                "quantity": 10,
                "price": 150.0
            },
            {
                "symbol": "MSFT",
                "type": "stock",
                "quantity": 5,
                "price": 300.0
            }
        ]
    }


def test_intake_agent_normalization(sample_raw_portfolio):
    """Test IntakeAgent normalizes portfolio"""
    agent = IntakeAgent()
    
    normalized = agent.process(sample_raw_portfolio)
    
    assert isinstance(normalized, NormalizedPortfolio)
    assert normalized.name == "Test Portfolio"
    assert len(normalized.positions) == 2
    assert agent.status == AgentStatus.COMPLETED
    
    # Check normalization
    for pos in normalized.positions:
        assert pos.current_price is not None
        assert pos.purchase_price is not None


def test_intake_agent_validation_missing_fields():
    """Test IntakeAgent validates required fields"""
    agent = IntakeAgent()
    
    bad_portfolio = {
        "name": "Bad Portfolio",
        "assets": [
            {"symbol": "AAPL"}  # Missing quantity
        ]
    }
    
    with pytest.raises(ValueError, match="missing required fields"):
        agent.process(bad_portfolio)
    
    assert agent.status == AgentStatus.FAILED


def test_intake_agent_option_validation():
    """Test IntakeAgent validates option fields"""
    agent = IntakeAgent()
    
    option_portfolio = {
        "name": "Option Portfolio",
        "assets": [
            {
                "symbol": "AAPL-CALL",
                "type": "option",
                "quantity": 1,
                "S": 150.0,
                "K": 155.0
                # Missing T, r, sigma
            }
        ]
    }
    
    with pytest.raises(ValueError, match="Option position missing"):
        agent.process(option_portfolio)


def test_risk_agent_calculation():
    """Test RiskAgent calculates metrics"""
    # First normalize with IntakeAgent
    raw_portfolio = {
        "name": "Test",
        "assets": [
            {"symbol": "AAPL", "type": "stock", "quantity": 10, "price": 150.0}
        ]
    }
    
    intake = IntakeAgent()
    normalized = intake.process(raw_portfolio)
    
    # Then calculate risk
    risk_agent = RiskAgent()
    metrics = risk_agent.process(normalized)
    
    assert isinstance(metrics, RiskMetrics)
    assert metrics.total_value == 1500.0
    assert metrics.asset_count == 1
    assert metrics.var_parametric is not None
    assert risk_agent.status == AgentStatus.COMPLETED


def test_risk_agent_with_options():
    """Test RiskAgent with options calculates Greeks"""
    raw_portfolio = {
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
                "price": 5.0
            }
        ]
    }
    
    intake = IntakeAgent()
    normalized = intake.process(raw_portfolio)
    
    risk_agent = RiskAgent()
    metrics = risk_agent.process(normalized)
    
    assert metrics.portfolio_greeks is not None
    assert "delta" in metrics.portfolio_greeks


def test_report_agent_generation():
    """Test ReportAgent generates report"""
    # Create mock metrics
    metrics = RiskMetrics(
        total_pnl=100.0,
        total_value=1500.0,
        asset_count=1,
        var_parametric=25.0,
        var_confidence=0.95
    )
    
    normalized = NormalizedPortfolio(
        name="Test Portfolio",
        positions=[
            Position(symbol="AAPL", type="stock", quantity=10, price=150.0)
        ]
    )
    
    # Use MockProvider for deterministic output
    mock_llm = MockProvider()
    report_agent = ReportAgent(llm_provider=mock_llm)
    
    report = report_agent.process(normalized, metrics)
    
    assert report.portfolio_name == "Test Portfolio"
    assert report.summary
    assert len(report.recommendations) > 0
    assert report.html_report is not None
    assert "<!DOCTYPE html>" in report.html_report
    assert report_agent.status == AgentStatus.COMPLETED


def test_report_agent_recommendations():
    """Test ReportAgent generates deterministic recommendations"""
    metrics_positive = RiskMetrics(
        total_pnl=100.0,
        total_value=1000.0,
        asset_count=1
    )
    
    normalized = NormalizedPortfolio(
        name="Test",
        positions=[Position(symbol="AAPL", type="stock", quantity=10, price=100.0)]
    )
    
    mock_llm = MockProvider()
    agent = ReportAgent(llm_provider=mock_llm)
    
    report = agent.process(normalized, metrics_positive)
    
    # Should recommend taking profits
    assert any("profit" in r.lower() for r in report.recommendations)


def test_multi_agent_coordinator_full_flow(sample_raw_portfolio):
    """Test full multi-agent coordination"""
    coordinator = MultiAgentCoordinator(llm_provider=MockProvider())
    
    report = coordinator.execute(sample_raw_portfolio)
    
    assert report.portfolio_name == "Test Portfolio"
    assert report.risk_metrics.total_value == 3000.0
    assert len(coordinator.handoffs) == 2  # Intake->Risk, Risk->Report
    
    # Check audit trail
    audit = coordinator.get_audit_trail()
    assert len(audit) == 2
    assert all("hash" in entry for entry in audit)


def test_handoff_logging():
    """Test that handoffs are logged with hashes"""
    coordinator = MultiAgentCoordinator(llm_provider=MockProvider())
    
    portfolio = {
        "name": "Test",
        "assets": [
            {"symbol": "AAPL", "type": "stock", "quantity": 10, "price": 150.0}
        ]
    }
    
    coordinator.execute(portfolio)
    
    handoffs = coordinator.handoffs
    assert len(handoffs) >= 2
    
    for handoff in handoffs:
        assert handoff.hash
        assert len(handoff.hash) == 64  # SHA256 hash
        assert handoff.from_agent
        assert handoff.to_agent


def test_determinism_multi_agent(sample_raw_portfolio):
    """Test that multi-agent execution is deterministic"""
    # Run multiple times
    results = []
    for _ in range(3):
        coordinator = MultiAgentCoordinator(llm_provider=MockProvider())
        report = coordinator.execute(sample_raw_portfolio)
        results.append({
            "total_value": report.risk_metrics.total_value,
            "total_pnl": report.risk_metrics.total_pnl,
            "summary": report.summary
        })
    
    # All metrics should be identical
    assert all(r["total_value"] == results[0]["total_value"] for r in results)
    assert all(r["total_pnl"] == results[0]["total_pnl"] for r in results)
    assert all(r["summary"] == results[0]["summary"] for r in results)


def test_typed_schemas():
    """Test that all agent outputs use typed schemas"""
    # Position
    pos = Position(symbol="AAPL", type="stock", quantity=10, price=150.0)
    assert pos.symbol == "AAPL"
    
    # NormalizedPortfolio
    portfolio = NormalizedPortfolio(name="Test", positions=[pos])
    assert len(portfolio.positions) == 1
    
    # RiskMetrics
    metrics = RiskMetrics(
        total_pnl=100.0,
        total_value=1500.0,
        asset_count=1
    )
    assert metrics.total_value == 1500.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
