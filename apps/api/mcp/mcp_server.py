"""
Azure MCP Server - Model Context Protocol Server for RiskCanvas
Exposes risk analytics tools via MCP interface
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

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


class MCPServer:
    """MCP Server implementing JSON-RPC protocol"""
    
    def __init__(self):
        self.tools = {
            "price_option": {
                "description": "Price a European option using Black-Scholes model",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "S": {"type": "number", "description": "Current stock price"},
                        "K": {"type": "number", "description": "Strike price"},
                        "T": {"type": "number", "description": "Time to maturity (years)"},
                        "r": {"type": "number", "description": "Risk-free rate"},
                        "sigma": {"type": "number", "description": "Volatility"},
                        "option_type": {"type": "string", "enum": ["call", "put"], "default": "call"}
                    },
                    "required": ["S", "K", "T", "r", "sigma"]
                }
            },
            "portfolio_analyze": {
                "description": "Analyze portfolio metrics including P&L and Greeks",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "positions": {
                            "type": "array",
                            "description": "List of portfolio positions",
                            "items": {"type": "object"}
                        }
                    },
                    "required": ["positions"]
                }
            },
            "risk_var": {
                "description": "Calculate Value at Risk",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "portfolio_value": {"type": "number"},
                        "method": {"type": "string", "enum": ["parametric", "historical"], "default": "parametric"},
                        "volatility": {"type": "number", "description": "Required for parametric"},
                        "confidence_level": {"type": "number", "default": 0.95},
                        "time_horizon_days": {"type": "integer", "default": 1},
                        "historical_returns": {"type": "array", "items": {"type": "number"}}
                    },
                    "required": ["portfolio_value"]
                }
            },
            "scenario_run": {
                "description": "Run stress test scenarios",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "positions": {"type": "array", "items": {"type": "object"}},
                        "scenarios": {"type": "array", "items": {"type": "object"}}
                    },
                    "required": ["positions", "scenarios"]
                }
            },
            "generate_report": {
                "description": "Generate comprehensive risk report",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "portfolio": {"type": "object"}
                    },
                    "required": ["portfolio"]
                }
            }
        }
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools"""
        return [
            {
                "name": name,
                "description": spec["description"],
                "parameters": spec["parameters"]
            }
            for name, spec in self.tools.items()
        ]
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool with given arguments.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
        
        Returns:
            Tool execution result
        """
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        # Execute the tool
        if tool_name == "price_option":
            return self._tool_price_option(arguments)
        elif tool_name == "portfolio_analyze":
            return self._tool_portfolio_analyze(arguments)
        elif tool_name == "risk_var":
            return self._tool_risk_var(arguments)
        elif tool_name == "scenario_run":
            return self._tool_scenario_run(arguments)
        elif tool_name == "generate_report":
            return self._tool_generate_report(arguments)
        else:
            raise ValueError(f"Tool not implemented: {tool_name}")
    
    def _tool_price_option(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute price_option tool"""
        price = price_option(
            S=args["S"],
            K=args["K"],
            T=args["T"],
            r=args["r"],
            sigma=args["sigma"],
            option_type=args.get("option_type", "call")
        )
        
        greeks = calculate_greeks(
            S=args["S"],
            K=args["K"],
            T=args["T"],
            r=args["r"],
            sigma=args["sigma"],
            option_type=args.get("option_type", "call")
        )
        
        return {
            "price": price,
            "greeks": greeks
        }
    
    def _tool_portfolio_analyze(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute portfolio_analyze tool"""
        positions = args["positions"]
        
        total_pnl = portfolio_pnl(positions)
        
        total_value = 0.0
        for pos in positions:
            current_price = pos.get("current_price", pos.get("price", 0))
            quantity = pos.get("quantity", 0)
            total_value += current_price * quantity
        
        greeks = None
        if any(p.get("type") == "option" for p in positions):
            greeks = portfolio_greeks(positions)
        
        return {
            "total_pnl": total_pnl,
            "total_value": total_value,
            "asset_count": len(positions),
            "greeks": greeks
        }
    
    def _tool_risk_var(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute risk_var tool"""
        method = args.get("method", "parametric")
        
        if method == "parametric":
            if "volatility" not in args:
                raise ValueError("volatility required for parametric VaR")
            
            var_value = var_parametric(
                portfolio_value=args["portfolio_value"],
                volatility=args["volatility"],
                confidence_level=args.get("confidence_level", 0.95),
                time_horizon_days=args.get("time_horizon_days", 1)
            )
        else:
            if "historical_returns" not in args:
                raise ValueError("historical_returns required for historical VaR")
            
            var_value = var_historical(
                current_value=args["portfolio_value"],
                historical_returns=args["historical_returns"],
                confidence_level=args.get("confidence_level", 0.95)
            )
        
        return {
            "method": method,
            "var_value": var_value,
            "confidence_level": args.get("confidence_level", 0.95)
        }
    
    def _tool_scenario_run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute scenario_run tool"""
        positions = args["positions"]
        scenarios = args["scenarios"]
        
        results = scenario_run(positions, scenarios)
        
        return {
            "scenarios": results
        }
    
    def _tool_generate_report(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute generate_report tool"""
        portfolio = args["portfolio"]
        positions = portfolio.get("assets", [])
        
        total_pnl = portfolio_pnl(positions)
        
        total_value = 0.0
        for pos in positions:
            current_price = pos.get("current_price", pos.get("price", 0))
            quantity = pos.get("quantity", 0)
            total_value += current_price * quantity
        
        greeks = None
        if any(p.get("type") == "option" for p in positions):
            greeks = portfolio_greeks(positions)
        
        return {
            "portfolio_id": portfolio.get("id"),
            "portfolio_name": portfolio.get("name"),
            "total_pnl": total_pnl,
            "total_value": total_value,
            "greeks": greeks
        }
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle JSON-RPC request.
        
        Args:
            request: JSON-RPC request
        
        Returns:
            JSON-RPC response
        """
        jsonrpc = request.get("jsonrpc")
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        if jsonrpc != "2.0":
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32600,
                    "message": "Invalid Request"
                },
                "id": request_id
            }
        
        try:
            if method == "tools/list":
                result = self.list_tools()
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                result = self.call_tool(tool_name, arguments)
            else:
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    },
                    "id": request_id
                }
            
            return {
                "jsonrpc": "2.0",
                "result": result,
                "id": request_id
            }
        
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": str(e)
                },
                "id": request_id
            }
    
    def run_stdio(self):
        """Run server in stdio mode for MCP protocol"""
        print("MCP Server started (stdio mode)", file=sys.stderr)
        print(f"Available tools: {len(self.tools)}", file=sys.stderr)
        
        for line in sys.stdin:
            try:
                request = json.loads(line.strip())
                response = self.handle_request(request)
                print(json.dumps(response), flush=True)
            except json.JSONDecodeError as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {str(e)}"
                    },
                    "id": None
                }
                print(json.dumps(error_response), flush=True)
            except Exception as e:
                print(f"Server error: {str(e)}", file=sys.stderr)


def main():
    """Main entry point"""
    server = MCPServer()
    server.run_stdio()


if __name__ == "__main__":
    main()
