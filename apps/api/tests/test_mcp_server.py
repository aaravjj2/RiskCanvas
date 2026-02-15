"""
Test suite for MCP Server
"""

import pytest
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.mcp_server import MCPServer


@pytest.fixture
def mcp_server():
    """Create MCP server instance"""
    return MCPServer()


def test_list_tools(mcp_server):
    """Test listing available tools"""
    tools = mcp_server.list_tools()
    
    assert len(tools) == 5
    assert any(t["name"] == "price_option" for t in tools)
    assert any(t["name"] == "portfolio_analyze" for t in tools)
    assert any(t["name"] == "risk_var" for t in tools)
    assert any(t["name"] == "scenario_run" for t in tools)
    assert any(t["name"] == "generate_report" for t in tools)
    
    # Check tool structure
    for tool in tools:
        assert "name" in tool
        assert "description" in tool
        assert "parameters" in tool


def test_call_price_option(mcp_server):
    """Test calling price_option tool"""
    args = {
        "S": 100.0,
        "K": 105.0,
        "T": 0.25,
        "r": 0.05,
        "sigma": 0.2,
        "option_type": "call"
    }
    
    result = mcp_server.call_tool("price_option", args)
    
    assert "price" in result
    assert "greeks" in result
    assert result["price"] > 0
    assert "delta" in result["greeks"]


def test_call_portfolio_analyze(mcp_server):
    """Test calling portfolio_analyze tool"""
    args = {
        "positions": [
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
    
    result = mcp_server.call_tool("portfolio_analyze", args)
    
    assert "total_pnl" in result
    assert "total_value" in result
    assert "asset_count" in result
    assert result["total_pnl"] == 100.0


def test_call_risk_var(mcp_server):
    """Test calling risk_var tool"""
    args = {
        "portfolio_value": 1000000.0,
        "method": "parametric",
        "volatility": 0.15,
        "confidence_level": 0.95
    }
    
    result = mcp_server.call_tool("risk_var", args)
    
    assert "method" in result
    assert "var_value" in result
    assert result["var_value"] > 0


def test_call_scenario_run(mcp_server):
    """Test calling scenario_run tool"""
    args = {
        "positions": [
            {
                "symbol": "AAPL",
                "type": "stock",
                "quantity": 100,
                "current_price": 150.0
            }
        ],
        "scenarios": [
            {
                "name": "Crash",
                "shock_type": "price",
                "parameters": {"price_change_pct": -20.0}
            }
        ]
    }
    
    result = mcp_server.call_tool("scenario_run", args)
    
    assert "scenarios" in result
    assert len(result["scenarios"]) == 1


def test_invalid_tool(mcp_server):
    """Test calling invalid tool"""
    with pytest.raises(ValueError, match="Unknown tool"):
        mcp_server.call_tool("invalid_tool", {})


def test_jsonrpc_list_tools(mcp_server):
    """Test JSON-RPC tools/list request"""
    request = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 1
    }
    
    response = mcp_server.handle_request(request)
    
    assert response["jsonrpc"] == "2.0"
    assert "result" in response
    assert response["id"] == 1
    assert len(response["result"]) == 5


def test_jsonrpc_call_tool(mcp_server):
    """Test JSON-RPC tools/call request"""
    request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "price_option",
            "arguments": {
                "S": 100.0,
                "K": 105.0,
                "T": 0.25,
                "r": 0.05,
                "sigma": 0.2
            }
        },
        "id": 2
    }
    
    response = mcp_server.handle_request(request)
    
    assert response["jsonrpc"] == "2.0"
    assert "result" in response
    assert response["id"] == 2
    assert "price" in response["result"]


def test_jsonrpc_invalid_method(mcp_server):
    """Test JSON-RPC invalid method"""
    request = {
        "jsonrpc": "2.0",
        "method": "invalid/method",
        "id": 3
    }
    
    response = mcp_server.handle_request(request)
    
    assert response["jsonrpc"] == "2.0"
    assert "error" in response
    assert response["error"]["code"] == -32601


def test_jsonrpc_invalid_version(mcp_server):
    """Test JSON-RPC invalid version"""
    request = {
        "jsonrpc": "1.0",
        "method": "tools/list",
        "id": 4
    }
    
    response = mcp_server.handle_request(request)
    
    assert "error" in response
    assert response["error"]["code"] == -32600


def test_determinism(mcp_server):
    """Test that tool calls are deterministic"""
    args = {
        "S": 100.0,
        "K": 105.0,
        "T": 0.25,
        "r": 0.05,
        "sigma": 0.2
    }
    
    # Call multiple times
    results = [mcp_server.call_tool("price_option", args) for _ in range(5)]
    
    # Convert to JSON for comparison
    json_results = [json.dumps(r, sort_keys=True) for r in results]
    
    # All should be identical
    assert len(set(json_results)) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
