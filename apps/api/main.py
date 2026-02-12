from fastapi import FastAPI
import json
import os
from datetime import datetime

app = FastAPI()

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.get("/export")
async def export_report():
    """
    Export a JSON report of portfolio data to artifacts/ directory.
    This is a stub implementation that creates a skeleton report.
    """
    # Ensure artifacts directory exists
    artifacts_dir = "artifacts"
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