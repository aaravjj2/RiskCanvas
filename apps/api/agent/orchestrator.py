"""
Agent Orchestrator - Deterministic Planner and Executor
"""

import json
import hashlib
from typing import List, Dict, Any, Literal
from enum import Enum
from pydantic import BaseModel, Field
import sys
from pathlib import Path

# Add engine to path
engine_path = str(Path(__file__).parent.parent.parent.parent / "packages" / "engine")
if engine_path not in sys.path:
    sys.path.insert(0, engine_path)

from src import (
    price_option,
    calculate_greeks,
    portfolio_pnl,
    portfolio_greeks,
    var_parametric,
    var_historical,
    scenario_run,
)


class ToolName(str, Enum):
    """Allowed tools for agent execution"""
    PRICE_OPTION = "price_option"
    ANALYZE_PORTFOLIO = "analyze_portfolio"
    CALCULATE_VAR = "calculate_var"
    RUN_SCENARIOS = "run_scenarios"
    GENERATE_REPORT = "generate_report"


class StepStatus(str, Enum):
    """Step execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PlanStep(BaseModel):
    """A single step in the execution plan"""
    step_id: int
    tool: ToolName
    description: str
    inputs: Dict[str, Any]
    depends_on: List[int] = Field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    output: Any = None
    error: str = None


class ExecutionPlan(BaseModel):
    """Complete execution plan"""
    goal: str
    steps: List[PlanStep]
    total_steps: int


class AuditLogEntry(BaseModel):
    """Single audit log entry"""
    step_id: int
    tool: str
    inputs_hash: str
    outputs_hash: str
    status: str
    error: str = None


class ExecutionResult(BaseModel):
    """Result of plan execution"""
    goal: str
    success: bool
    steps_completed: int
    steps_failed: int
    outputs: Dict[str, Any]
    audit_log: List[AuditLogEntry]


class OrchestratorAgent:
    """
    Deterministic orchestrator that creates and executes structured plans
    """
    
    def __init__(self):
        self.allowed_tools = set(ToolName)
    
    def create_plan(self, goal: str, portfolio: Dict[str, Any]) -> ExecutionPlan:
        """
        Create a structured execution plan based on goal.
        
        Args:
            goal: User's goal (e.g., "analyze portfolio risk")
            portfolio: Portfolio data
        
        Returns:
            ExecutionPlan with ordered steps
        """
        steps = []
        
        goal_lower = goal.lower()
        
        # Determine plan based on goal keywords (deterministic mapping)
        if "analyze" in goal_lower or "full" in goal_lower or "comprehensive" in goal_lower:
            # Full analysis plan
            steps.append(PlanStep(
                step_id=1,
                tool=ToolName.ANALYZE_PORTFOLIO,
                description="Analyze portfolio metrics (P&L, value, Greeks)",
                inputs={"portfolio": portfolio}
            ))
            
            steps.append(PlanStep(
                step_id=2,
                tool=ToolName.CALCULATE_VAR,
                description="Calculate Value at Risk",
                inputs={
                    "portfolio_value": 0,  # Will be filled from step 1
                    "method": "parametric",
                    "volatility": 0.15,
                    "confidence_level": 0.95
                },
                depends_on=[1]
            ))
            
            steps.append(PlanStep(
                step_id=3,
                tool=ToolName.RUN_SCENARIOS,
                description="Run stress test scenarios",
                inputs={
                    "positions": portfolio.get("assets", []),
                    "scenarios": [
                        {
                            "name": "Market Crash -20%",
                            "shock_type": "price",
                            "parameters": {"price_change_pct": -20.0}
                        },
                        {
                            "name": "Volatility Spike +50%",
                            "shock_type": "volatility",
                            "parameters": {"volatility_change_pct": 50.0}
                        }
                    ]
                }
            ))
            
            steps.append(PlanStep(
                step_id=4,
                tool=ToolName.GENERATE_REPORT,
                description="Generate comprehensive report",
                inputs={"portfolio": portfolio},
                depends_on=[1, 2, 3]
            ))
        
        elif "var" in goal_lower or "risk" in goal_lower:
            # VaR-focused plan
            steps.append(PlanStep(
                step_id=1,
                tool=ToolName.ANALYZE_PORTFOLIO,
                description="Get portfolio value",
                inputs={"portfolio": portfolio}
            ))
            
            steps.append(PlanStep(
                step_id=2,
                tool=ToolName.CALCULATE_VAR,
                description="Calculate VaR",
                inputs={
                    "portfolio_value": 0,
                    "method": "parametric",
                    "volatility": 0.15,
                    "confidence_level": 0.95
                },
                depends_on=[1]
            ))
        
        elif "scenario" in goal_lower or "stress" in goal_lower:
            # Scenario-focused plan
            steps.append(PlanStep(
                step_id=1,
                tool=ToolName.RUN_SCENARIOS,
                description="Run stress scenarios",
                inputs={
                    "positions": portfolio.get("assets", []),
                    "scenarios": [
                        {
                            "name": "Market Crash -20%",
                            "shock_type": "price",
                            "parameters": {"price_change_pct": -20.0}
                        },
                        {
                            "name": "Market Rally +15%",
                            "shock_type": "price",
                            "parameters": {"price_change_pct": 15.0}
                        }
                    ]
                }
            ))
        
        elif "report" in goal_lower:
            # Report generation plan
            steps.append(PlanStep(
                step_id=1,
                tool=ToolName.GENERATE_REPORT,
                description="Generate portfolio report",
                inputs={"portfolio": portfolio}
            ))
        
        else:
            # Default: basic analysis
            steps.append(PlanStep(
                step_id=1,
                tool=ToolName.ANALYZE_PORTFOLIO,
                description="Analyze portfolio",
                inputs={"portfolio": portfolio}
            ))
        
        return ExecutionPlan(
            goal=goal,
            steps=steps,
            total_steps=len(steps)
        )
    
    def execute_plan(self, plan: ExecutionPlan) -> ExecutionResult:
        """
        Execute the plan deterministically.
        
        Args:
            plan: ExecutionPlan to execute
        
        Returns:
            ExecutionResult with outputs and audit log
        """
        audit_log = []
        outputs = {}
        steps_completed = 0
        steps_failed = 0
        
        # Execute steps in order
        for step in plan.steps:
            # Check dependencies
            if not self._dependencies_met(step, plan.steps):
                step.status = StepStatus.SKIPPED
                continue
            
            step.status = StepStatus.RUNNING
            
            try:
                # Execute the tool
                result = self._execute_tool(step.tool, step.inputs, outputs)
                
                step.output = result
                step.status = StepStatus.COMPLETED
                steps_completed += 1
                
                # Store output for dependent steps
                outputs[f"step_{step.step_id}"] = result
                
                # Audit log entry
                audit_entry = AuditLogEntry(
                    step_id=step.step_id,
                    tool=step.tool.value,
                    inputs_hash=self._hash_data(step.inputs),
                    outputs_hash=self._hash_data(result),
                    status="completed"
                )
                audit_log.append(audit_entry)
                
            except Exception as e:
                step.status = StepStatus.FAILED
                step.error = str(e)
                steps_failed += 1
                
                audit_entry = AuditLogEntry(
                    step_id=step.step_id,
                    tool=step.tool.value,
                    inputs_hash=self._hash_data(step.inputs),
                    outputs_hash="",
                    status="failed",
                    error=str(e)
                )
                audit_log.append(audit_entry)
        
        success = steps_failed == 0 and steps_completed > 0
        
        return ExecutionResult(
            goal=plan.goal,
            success=success,
            steps_completed=steps_completed,
            steps_failed=steps_failed,
            outputs=outputs,
            audit_log=audit_log
        )
    
    def _dependencies_met(self, step: PlanStep, all_steps: List[PlanStep]) -> bool:
        """Check if step dependencies are met"""
        for dep_id in step.depends_on:
            dep_step = next((s for s in all_steps if s.step_id == dep_id), None)
            if dep_step is None or dep_step.status != StepStatus.COMPLETED:
                return False
        return True
    
    def _execute_tool(self, tool: ToolName, inputs: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """
        Execute a specific tool with given inputs.
        
        Args:
            tool: Tool to execute
            inputs: Tool inputs
            context: Context from previous steps
        
        Returns:
            Tool output
        """
        if tool == ToolName.PRICE_OPTION:
            return self._tool_price_option(inputs)
        
        elif tool == ToolName.ANALYZE_PORTFOLIO:
            return self._tool_analyze_portfolio(inputs)
        
        elif tool == ToolName.CALCULATE_VAR:
            return self._tool_calculate_var(inputs, context)
        
        elif tool == ToolName.RUN_SCENARIOS:
            return self._tool_run_scenarios(inputs)
        
        elif tool == ToolName.GENERATE_REPORT:
            return self._tool_generate_report(inputs, context)
        
        else:
            raise ValueError(f"Unknown tool: {tool}")
    
    def _tool_price_option(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute price_option tool"""
        price = price_option(
            S=inputs["S"],
            K=inputs["K"],
            T=inputs["T"],
            r=inputs["r"],
            sigma=inputs["sigma"],
            option_type=inputs.get("option_type", "call")
        )
        
        greeks = calculate_greeks(
            S=inputs["S"],
            K=inputs["K"],
            T=inputs["T"],
            r=inputs["r"],
            sigma=inputs["sigma"],
            option_type=inputs.get("option_type", "call")
        )
        
        return {
            "price": price,
            "greeks": greeks
        }
    
    def _tool_analyze_portfolio(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analyze_portfolio tool"""
        portfolio = inputs["portfolio"]
        positions = portfolio.get("assets", [])
        
        # Calculate P&L
        total_pnl = portfolio_pnl(positions)
        
        # Calculate value
        total_value = 0.0
        for pos in positions:
            current_price = pos.get("current_price", pos.get("price", 0))
            quantity = pos.get("quantity", 0)
            total_value += current_price * quantity
        
        # Calculate Greeks
        greeks = None
        if any(p.get("type") == "option" for p in positions):
            greeks = portfolio_greeks(positions)
        
        return {
            "total_pnl": total_pnl,
            "total_value": total_value,
            "asset_count": len(positions),
            "greeks": greeks
        }
    
    def _tool_calculate_var(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute calculate_var tool"""
        # Get portfolio value from context if needed
        portfolio_value = inputs.get("portfolio_value", 0)
        if portfolio_value == 0 and "step_1" in context:
            portfolio_value = context["step_1"].get("total_value", 0)
        
        method = inputs.get("method", "parametric")
        
        if method == "parametric":
            var_value = var_parametric(
                portfolio_value=portfolio_value,
                volatility=inputs.get("volatility", 0.15),
                confidence_level=inputs.get("confidence_level", 0.95),
                time_horizon_days=inputs.get("time_horizon_days", 1)
            )
        else:
            var_value = var_historical(
                current_value=portfolio_value,
                historical_returns=inputs.get("historical_returns", []),
                confidence_level=inputs.get("confidence_level", 0.95)
            )
        
        return {
            "method": method,
            "var_value": var_value,
            "confidence_level": inputs.get("confidence_level", 0.95)
        }
    
    def _tool_run_scenarios(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute run_scenarios tool"""
        positions = inputs["positions"]
        scenarios = inputs["scenarios"]
        
        results = scenario_run(positions, scenarios)
        
        return {
            "scenarios": results
        }
    
    def _tool_generate_report(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute generate_report tool"""
        portfolio = inputs["portfolio"]
        
        # Get analysis from context
        analysis = context.get("step_1", {})
        var_data = context.get("step_2", {})
        scenario_data = context.get("step_3", {})
        
        return {
            "portfolio_id": portfolio.get("id"),
            "portfolio_name": portfolio.get("name"),
            "analysis": analysis,
            "var": var_data,
            "scenarios": scenario_data
        }
    
    def _hash_data(self, data: Any) -> str:
        """Create deterministic hash of data"""
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()
