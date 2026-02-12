from fastapi import FastAPI
import json
import os
from datetime import datetime
from typing import List, Dict, Any
from models.pricing import portfolio_pl, portfolio_delta_exposure, portfolio_net_delta_exposure, portfolio_gross_exposure, portfolio_sector_aggregation

app = FastAPI()

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.post("/portfolio/report")
async def generate_portfolio_report(portfolio_data: Dict[str, Any]):
    """
    Generate a portfolio report from provided portfolio data.

    Args:
        portfolio_data: Dictionary containing portfolio information with assets

    Returns:
        Dictionary with portfolio summary including P&L and delta exposure
    """
    # Calculate portfolio metrics
    positions = portfolio_data.get("assets", [])

    # Calculate total profit/loss
    total_pl = portfolio_pl(positions)

    # Calculate total delta exposure
    total_delta_exposure = portfolio_delta_exposure(positions)

    # Calculate net delta exposure
    net_delta_exposure = portfolio_net_delta_exposure(positions)

    # Calculate gross exposure
    gross_exposure = portfolio_gross_exposure(positions)

    # Create report
    report = {
        "portfolio_id": portfolio_data.get("id"),
        "portfolio_name": portfolio_data.get("name"),
        "generated_at": datetime.now().isoformat(),
        "metrics": {
            "total_profit_loss": total_pl,
            "total_delta_exposure": total_delta_exposure,
            "net_delta_exposure": net_delta_exposure,
            "gross_exposure": gross_exposure,
            "total_value": portfolio_data.get("total_value", 0),
            "asset_count": len(positions)
        },
        "assets": positions
    }

    return report


@app.post("/portfolio/aggregation/sector")
async def portfolio_sector_aggregation_endpoint(portfolio_data: Dict[str, Any]):
    """
    Generate sector aggregation report for a portfolio.

    Args:
        portfolio_data: Dictionary containing portfolio information with assets

    Returns:
        Dictionary with sector aggregation data
    """
    positions = portfolio_data.get("assets", [])

    # Calculate sector aggregation
    sector_data = portfolio_sector_aggregation(positions)

    # Create report
    report = {
        "portfolio_id": portfolio_data.get("id"),
        "portfolio_name": portfolio_data.get("name"),
        "generated_at": datetime.now().isoformat(),
        "sector_data": sector_data
    }

    return report


@app.get("/portfolio/aggregation/summary")
async def portfolio_aggregation_summary():
    """
    Generate a summary of all portfolios with aggregated metrics.

    Returns:
        Dictionary with aggregated portfolio metrics
    """
    # This is a stub implementation - in a real application, this would
    # read from a database or load portfolio data from fixtures

    # For now, we'll return some sample data
    return {
        "generated_at": datetime.now().isoformat(),
        "aggregation_type": "portfolio_summary",
        "metrics": {
            "total_portfolios": 3,
            "total_value": 12534.75,
            "total_delta_exposure": 0.0,
            "net_delta_exposure": 0.0,
            "gross_exposure": 0.0
        }
    }

@app.get("/export")
async def export_report():
    """
    Export a JSON report of portfolio data to artifacts/ directory.
    This is a stub implementation that creates a skeleton report.
    """
    # Ensure artifacts directory exists at repo root
    artifacts_dir = "../artifacts"
    os.makedirs(artifacts_dir, exist_ok=True)

    # Create a basic report structure (stub)
    report = {
        "exported_at": datetime.now().isoformat(),
        "report_type": "portfolio_summary",
        "data": {
            "portfolios": [
                {
                    "id": 1,
                    "name": "Tech Growth Portfolio",
                    "description": "A portfolio focused on technology sector growth stocks",
                    "assets": [
                        {
                            "symbol": "AAPL",
                            "name": "Apple Inc.",
                            "type": "stock",
                            "quantity": 10,
                            "price": 150.25
                        },
                        {
                            "symbol": "MSFT",
                            "name": "Microsoft Corporation",
                            "type": "stock",
                            "quantity": 5,
                            "price": 300.50
                        }
                    ],
                    "total_value": 3002.50,
                    "created_at": "2023-01-15T10:30:00Z"
                },
                {
                    "id": 2,
                    "name": "Balanced Income Portfolio",
                    "description": "A diversified portfolio focused on steady income generation",
                    "assets": [
                        {
                            "symbol": "KO",
                            "name": "Coca-Cola Company",
                            "type": "stock",
                            "quantity": 20,
                            "price": 55.75
                        },
                        {
                            "symbol": "JNJ",
                            "name": "Johnson & Johnson",
                            "type": "stock",
                            "quantity": 15,
                            "price": 160.30
                        },
                        {
                            "symbol": "VZ",
                            "name": "Verizon Communications",
                            "type": "stock",
                            "quantity": 25,
                            "price": 40.10
                        }
                    ],
                    "total_value": 4528.25,
                    "created_at": "2023-03-22T14:15:00Z"
                },
                {
                    "id": 3,
                    "name": "Growth & Value Portfolio",
                    "description": "A mixed portfolio combining growth and value stocks",
                    "assets": [
                        {
                            "symbol": "TSLA",
                            "name": "Tesla, Inc.",
                            "type": "stock",
                            "quantity": 8,
                            "price": 250.00
                        },
                        {
                            "symbol": "BRK.B",
                            "name": "Berkshire Hathaway Inc.",
                            "type": "stock",
                            "quantity": 3,
                            "price": 300.00
                        },
                        {
                            "symbol": "SPY",
                            "name": "SPDR S&P 500 ETF Trust",
                            "type": "etf",
                            "quantity": 10,
                            "price": 400.50
                        }
                    ],
                    "total_value": 5004.00,
                    "created_at": "2023-06-10T09:45:00Z"
                }
            ],
            "summary": {
                "total_portfolios": 3,
                "total_value": 12534.75,
                "created_at": datetime.now().isoformat()
            }
        }
    }

    # Write the report to artifacts directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"portfolio_report_{timestamp}.json"
    filepath = os.path.join(artifacts_dir, filename)

    with open(filepath, 'w') as f:
        json.dump(report, f, indent=2)

    return {
        "message": f"Report exported successfully to {filepath}",
        "filename": filename
    }