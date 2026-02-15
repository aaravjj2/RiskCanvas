"""
Test suite for Orchestrator Agent
"""

import pytest
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.orchestrator import OrchestratorAgent, ExecutionPlan, ToolName, StepStatus


@pytest.fixture
def sample_portfolio():
    """Sample portfolio for testing"""
    return {
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


def test_create_plan_analyze_goal(sample_portfolio):
    """Test plan creation for 'analyze' goal"""
    agent = OrchestratorAgent()
    plan = agent.create_plan("analyze portfolio risk", sample_portfolio)
    
    assert isinstance(plan, ExecutionPlan)
    assert plan.goal == "analyze portfolio risk"
    assert plan.total_steps > 0
    assert len(plan.steps) == plan.total_steps
    
    # Should include analysis step
    assert any(s.tool == ToolName.ANALYZE_PORTFOLIO for s in plan.steps)


def test_create_plan_var_goal(sample_portfolio):
    """Test plan creation for 'var' goal"""
    agent = OrchestratorAgent()
    plan = agent.create_plan("calculate VaR", sample_portfolio)
    
    assert plan.total_steps >= 2
    assert any(s.tool == ToolName.CALCULATE_VAR for s in plan.steps)


def test_create_plan_scenario_goal(sample_portfolio):
    """Test plan creation for 'scenario' goal"""
    agent = OrchestratorAgent()
    plan = agent.create_plan("run stress test scenarios", sample_portfolio)
    
    assert any(s.tool == ToolName.RUN_SCENARIOS for s in plan.steps)


def test_create_plan_report_goal(sample_portfolio):
    """Test plan creation for 'report' goal"""
    agent = OrchestratorAgent()
    plan = agent.create_plan("generate report", sample_portfolio)
    
    assert any(s.tool == ToolName.GENERATE_REPORT for s in plan.steps)


def test_execute_plan_basic_analysis(sample_portfolio):
    """Test executing a basic analysis plan"""
    agent = OrchestratorAgent()
    plan = agent.create_plan("analyze portfolio", sample_portfolio)
    
    result = agent.execute_plan(plan)
    
    assert result.success
    assert result.steps_completed > 0
    assert result.steps_failed == 0
    assert len(result.audit_log) == result.steps_completed
    assert len(result.outputs) > 0


def test_execute_plan_full_analysis(sample_portfolio):
    """Test executing a full analysis plan"""
    agent = OrchestratorAgent()
    plan = agent.create_plan("comprehensive portfolio analysis", sample_portfolio)
    
    result = agent.execute_plan(plan)
    
    assert result.success
    assert result.steps_completed >= 4  # Analysis, VaR, Scenarios, Report
    assert "step_1" in result.outputs  # Analysis output
    
    # Check audit log
    assert all(entry.status == "completed" for entry in result.audit_log)
    assert all(entry.inputs_hash for entry in result.audit_log)
    assert all(entry.outputs_hash for entry in result.audit_log)


def test_plan_determinism(sample_portfolio):
    """Test that plan creation is deterministic"""
    agent = OrchestratorAgent()
    
    # Create same plan multiple times
    plans = [agent.create_plan("analyze portfolio", sample_portfolio) for _ in range(5)]
    
    # Convert to JSON for comparison
    plan_jsons = [json.dumps(p.model_dump(), sort_keys=True) for p in plans]
    
    # All should be identical
    assert len(set(plan_jsons)) == 1


def test_execution_determinism(sample_portfolio):
    """Test that execution is deterministic"""
    agent = OrchestratorAgent()
    plan = agent.create_plan("analyze portfolio", sample_portfolio)
    
    # Execute multiple times
    results = [agent.execute_plan(plan) for _ in range(3)]
    
    # All should succeed
    assert all(r.success for r in results)
    
    # Extract output hashes from audit logs
    output_hashes = [
        [entry.outputs_hash for entry in r.audit_log]
        for r in results
    ]
    
    # All hashes should be identical
    for i in range(1, len(output_hashes)):
        assert output_hashes[i] == output_hashes[0]


def test_whitelist_enforcement():
    """Test that only whitelisted tools can be used"""
    agent = OrchestratorAgent()
    
    # All tools in ToolName enum should be allowed
    assert ToolName.PRICE_OPTION in agent.allowed_tools
    assert ToolName.ANALYZE_PORTFOLIO in agent.allowed_tools
    assert ToolName.CALCULATE_VAR in agent.allowed_tools


def test_dependency_handling(sample_portfolio):
    """Test that step dependencies are handled correctly"""
    agent = OrchestratorAgent()
    plan = agent.create_plan("calculate VaR", sample_portfolio)
    
    # VaR step should depend on analysis step
    var_step = next((s for s in plan.steps if s.tool == ToolName.CALCULATE_VAR), None)
    assert var_step is not None
    assert len(var_step.depends_on) > 0
    
    # Execute plan
    result = agent.execute_plan(plan)
    
    # VaR calculation should use value from analysis step
    assert result.success
    assert "step_2" in result.outputs  # VaR output


def test_audit_log_completeness(sample_portfolio):
    """Test that audit log captures all necessary information"""
    agent = OrchestratorAgent()
    plan = agent.create_plan("analyze portfolio", sample_portfolio)
    
    result = agent.execute_plan(plan)
    
    for entry in result.audit_log:
        assert entry.step_id > 0
        assert entry.tool
        assert entry.inputs_hash
        assert entry.outputs_hash
        assert entry.status == "completed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
