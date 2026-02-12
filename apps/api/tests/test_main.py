import json
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