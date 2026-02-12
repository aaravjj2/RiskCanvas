import json
import os
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}

def test_fixture_loading():
    # Test that we can load fixture data
    with open("fixtures/portfolio_1.json") as f:
        portfolio = json.load(f)
        assert portfolio["id"] == 1
        assert portfolio["name"] == "Tech Growth Portfolio"
        assert len(portfolio["assets"]) == 2

def test_export_endpoint():
    # Test the export endpoint
    response = client.get("/export")
    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert "filename" in data
    assert data["message"].startswith("Report exported successfully to")

    # Verify the file was created
    filename = data["filename"]
    filepath = os.path.join("artifacts", filename)
    assert os.path.exists(filepath)

    # Verify the content is valid JSON
    with open(filepath, 'r') as f:
        report = json.load(f)
        assert "exported_at" in report
        assert "report_type" in report
        assert "data" in report
        assert "portfolios" in report["data"]
        assert len(report["data"]["portfolios"]) == 3