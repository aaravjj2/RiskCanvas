"""
MCP (Model Context Protocol) Server for RiskCanvas v2.2+
Exposes RiskCanvas tools as MCP endpoints for Agent Framework integration.
"""

import json
import hashlib
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Import RiskCanvas functions
from models.pricing import portfolio_pl, portfolio_var
from report_bundle import build_report_html, build_report_manifest
from hedge_engine import generate_hedge_candidates
from governance import run_eval_harness


# MCP Router
mcp_router = APIRouter(prefix="/mcp", tags=["mcp"])


class MCPTool(BaseModel):
    """MCP tool metadata"""
    name: str
    description: str
    input_schema: Dict[str, Any]


class MCPToolCallRequest(BaseModel):
    """MCP tool call request"""
    tool_name: str
    arguments: Dict[str, Any]


class MCPToolCallResponse(BaseModel):
    """MCP tool call response"""
    tool_name: str
    result: Any
    success: bool
    error: str | None = None


# Tool registry
MCP_TOOLS: List[MCPTool] = [
    MCPTool(
        name="portfolio_analyze",
        description="Analyze portfolio risk metrics (VaR, Greeks, PnL)",
        input_schema={
            "type": "object",
            "properties": {
                "portfolio": {
                    "type": "array",
                    "description": "List of positions with symbol, quantity, price",
                    "items": {"type": "object"}
                },
                "var_method": {
                    "type": "string",
                    "enum": ["parametric", "historical"],
                    "default": "parametric"
                }
            },
            "required": ["portfolio"]
        }
    ),
    MCPTool(
        name="report_build",
        description="Build HTML report with analysis results",
        input_schema={
            "type": "object",
            "properties": {
                "analysis_data": {
                    "type": "object",
                    "description": "Analysis results to include in report"
                },
                "title": {
                    "type": "string",
                    "default": "Risk Canvas Report"
                }
            },
            "required": ["analysis_data"]
        }
    ),
    MCPTool(
        name="hedge_suggest",
        description="Generate hedge recommendations for portfolio",
        input_schema={
            "type": "object",
            "properties": {
                "portfolio": {
                    "type": "array",
                    "description": "Portfolio positions"
                },
                "target_reduction": {
                    "type": "number",
                    "description": "Target risk reduction (0.0-1.0)",
                    "default": 0.3
                }
            },
            "required": ["portfolio"]
        }
    ),
    MCPTool(
        name="governance_eval_run",
        description="Run governance evaluation harness for agent config",
        input_schema={
            "type": "object",
            "properties": {
                "config_id": {
                    "type": "string",
                    "description": "Agent config ID to evaluate"
                },
                "test_cases": {
                    "type": "array",
                    "description": "Test cases for evaluation"
                }
            },
            "required": ["config_id"]
        }
    )
]


@mcp_router.get("/tools", response_model=List[MCPTool])
async def list_mcp_tools():
    """List all available MCP tools"""
    return MCP_TOOLS


@mcp_router.post("/tools/call", response_model=MCPToolCallResponse)
async def call_mcp_tool(request: MCPToolCallRequest):
    """
    Execute MCP tool with provided arguments.
    Routes to appropriate RiskCanvas function.
    """
    try:
        result = None
        
        if request.tool_name == "portfolio_analyze":
            # Call portfolio analysis
            portfolio = request.arguments.get("portfolio", [])
            var_method = request.arguments.get("var_method", "parametric")
            
            # Calculate PnL
            pl_result = portfolio_pl(portfolio)
            
            # Calculate VaR
            var_result = portfolio_var(portfolio, method=var_method)
            
            result = {
                "pnl": pl_result,
                "var": var_result,
                "asset_count": len(portfolio)
            }
        
        elif request.tool_name == "report_build":
            # Build report
            analysis_data = request.arguments.get("analysis_data", {})
            title = request.arguments.get("title", "Risk Canvas Report")
            
            html = build_report_html(analysis_data, title)
            manifest = build_report_manifest(analysis_data)
            
            result = {
                "html_length": len(html),
                "manifest": manifest
            }
        
        elif request.tool_name == "hedge_suggest":
            # Generate hedge recommendations
            portfolio = request.arguments.get("portfolio", [])
            target_reduction = request.arguments.get("target_reduction", 0.3)
            
            hedges = generate_hedge_candidates(portfolio, target_reduction)
            
            result = {
                "hedge_count": len(hedges),
                "hedges": hedges[:5]  # Return top 5
            }
        
        elif request.tool_name == "governance_eval_run":
            # Run governance evaluation
            config_id = request.arguments.get("config_id")
            
            eval_result = run_eval_harness(config_id)
            
            result = eval_result
        
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown tool: {request.tool_name}"
            )
        
        return MCPToolCallResponse(
            tool_name=request.tool_name,
            result=result,
            success=True
        )
    
    except Exception as e:
        return MCPToolCallResponse(
            tool_name=request.tool_name,
            result=None,
            success=False,
            error=str(e)
        )


@mcp_router.get("/health")
async def mcp_health():
    """MCP server health check"""
    return {
        "status": "healthy",
        "tool_count": len(MCP_TOOLS),
        "version": "2.2.0"
    }
