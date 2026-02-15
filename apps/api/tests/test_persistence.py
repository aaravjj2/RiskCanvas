"""
Tests for v1.1+ persistence features (Portfolio Library + Run History)
"""

import pytest
import json
from httpx import AsyncClient, ASGITransport
from main import app
from database import db, generate_portfolio_id, generate_run_id


@pytest.fixture(autouse=True)
def reset_database():
    """Reset database before each test"""
    # Database is already in-memory for pytest (see database.py)
    # Just ensure tables are created
    from sqlmodel import SQLModel, text
    SQLModel.metadata.create_all(db.engine)
    yield
    # Clear all data
    with db.get_session() as session:
        session.exec(text("DELETE FROM runs"))
        session.exec(text("DELETE FROM portfolios"))
        session.commit()


@pytest.fixture
def sample_portfolio():
    return {
        "id": "test-portfolio-1",
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
                "symbol": "GOOGL",
                "type": "stock",
                "quantity": 5,
                "price": 2800.0,
                "current_price": 2800.0,
                "purchase_price": 2700.0
            }
        ]
    }


@pytest.mark.asyncio
async def test_create_portfolio(sample_portfolio):
    """Test creating a portfolio"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/portfolios",
            json={"portfolio": sample_portfolio, "name": "My Test Portfolio", "tags": ["test", "sample"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert "portfolio_id" in data
        assert data["name"] == "My Test Portfolio"
        assert data["tags"] == ["test", "sample"]
        assert data["portfolio"] == sample_portfolio


@pytest.mark.asyncio
async def test_portfolio_id_determinism(sample_portfolio):
    """Test that same portfolio produces same portfolio_id"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response1 = await client.post("/portfolios", json={"portfolio": sample_portfolio})
        response2 = await client.post("/portfolios", json={"portfolio": sample_portfolio})
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Same portfolio should have same ID
        assert data1["portfolio_id"] == data2["portfolio_id"]


@pytest.mark.asyncio
async def test_list_portfolios(sample_portfolio):
    """Test listing portfolios"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create two portfolios
        await client.post("/portfolios", json={"portfolio": sample_portfolio, "name": "Portfolio 1"})
        
        sample_portfolio2 = {**sample_portfolio, "id": "test-portfolio-2"}
        await client.post("/portfolios", json={"portfolio": sample_portfolio2, "name": "Portfolio 2"})
        
        # List all
        response = await client.get("/portfolios")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


@pytest.mark.asyncio
async def test_get_portfolio(sample_portfolio):
    """Test getting individual portfolio"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create
        create_response = await client.post("/portfolios", json={"portfolio": sample_portfolio})
        portfolio_id = create_response.json()["portfolio_id"]
        
        # Get
        get_response = await client.get(f"/portfolios/{portfolio_id}")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["portfolio_id"] == portfolio_id


@pytest.mark.asyncio
async def test_delete_portfolio(sample_portfolio):
    """Test deleting portfolio"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create
        create_response = await client.post("/portfolios", json={"portfolio": sample_portfolio})
        portfolio_id = create_response.json()["portfolio_id"]
        
        # Delete
        delete_response = await client.delete(f"/portfolios/{portfolio_id}")
        assert delete_response.status_code == 200
        
        # Verify deleted
        get_response = await client.get(f"/portfolios/{portfolio_id}")
        assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_execute_run(sample_portfolio):
    """Test executing analysis run"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/runs/execute",
            json={"portfolio": sample_portfolio, "params": {"confidence_level": 0.95}}
        )
        assert response.status_code == 200
        data = response.json()
        assert "run_id" in data
        assert "portfolio_id" in data
        assert "output_hash" in data
        assert "outputs" in data
        assert data["outputs"]["pricing"]["portfolio_value"] > 0


@pytest.mark.asyncio
async def test_run_id_determinism(sample_portfolio):
    """Test that same portfolio + params produces same run_id"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        params = {"confidence_level": 0.95}
        
        response1 = await client.post("/runs/execute", json={"portfolio": sample_portfolio, "params": params})
        response2 = await client.post("/runs/execute", json={"portfolio": sample_portfolio, "params": params})
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Same inputs should produce same run_id
        assert data1["run_id"] == data2["run_id"]
        assert data1["output_hash"] == data2["output_hash"]


@pytest.mark.asyncio
async def test_list_runs(sample_portfolio):
    """Test listing runs"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Execute two runs
        await client.post("/runs/execute", json={"portfolio": sample_portfolio})
        
        sample_portfolio2 = {**sample_portfolio, "id": "test-portfolio-2"}
        await client.post("/runs/execute", json={"portfolio": sample_portfolio2})
        
        # List all runs
        response = await client.get("/runs")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


@pytest.mark.asyncio
async def test_list_runs_filtered(sample_portfolio):
    """Test listing runs filtered by portfolio_id"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create portfolio
        create_response = await client.post("/portfolios", json={"portfolio": sample_portfolio})
        portfolio_id = create_response.json()["portfolio_id"]
        
        # Execute run
        await client.post("/runs/execute", json={"portfolio_id": portfolio_id})
        
        # List runs for this portfolio
        response = await client.get(f"/runs?portfolio_id={portfolio_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["portfolio_id"] == portfolio_id


@pytest.mark.asyncio
async def test_get_run(sample_portfolio):
    """Test getting full run details"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Execute run
        execute_response = await client.post("/runs/execute", json={"portfolio": sample_portfolio})
        run_id = execute_response.json()["run_id"]
        
        # Get run
        get_response = await client.get(f"/runs/{run_id}")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["run_id"] == run_id
        assert "outputs" in data
        assert "pricing" in data["outputs"]
        assert "var" in data["outputs"]


@pytest.mark.asyncio
async def test_compare_runs(sample_portfolio):
    """Test comparing two runs"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Execute first run
        response1 = await client.post("/runs/execute", json={"portfolio": sample_portfolio})
        run_id_a = response1.json()["run_id"]
        
        # Modify portfolio and execute second run
        sample_portfolio2 = {**sample_portfolio}
        sample_portfolio2["assets"][0]["quantity"] = 20  # Double AAPL quantity
        response2 = await client.post("/runs/execute", json={"portfolio": sample_portfolio2})
        run_id_b = response2.json()["run_id"]
        
        # Compare
        compare_response = await client.post(
            "/runs/compare",
            json={"run_id_a": run_id_a, "run_id_b": run_id_b}
        )
        assert compare_response.status_code == 200
        data = compare_response.json()
        assert data["run_id_a"] == run_id_a
        assert data["run_id_b"] == run_id_b
        assert "deltas" in data
        assert "top_changes" in data
        
        # Portfolio value should have increased
        assert data["deltas"]["portfolio_value"]["delta"] > 0


@pytest.mark.asyncio
async def test_compare_runs_not_found():
    """Test comparing with invalid run IDs"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/runs/compare",
            json={"run_id_a": "invalid_id_a", "run_id_b": "invalid_id_b"}
        )
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_execute_run_with_portfolio_id(sample_portfolio):
    """Test executing run with existing portfolio_id"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create portfolio first
        create_response = await client.post("/portfolios", json={"portfolio": sample_portfolio})
        portfolio_id = create_response.json()["portfolio_id"]
        
        # Execute run with portfolio_id
        execute_response = await client.post(
            "/runs/execute",
            json={"portfolio_id": portfolio_id}
        )
        assert execute_response.status_code == 200
        data = execute_response.json()
        assert data["portfolio_id"] == portfolio_id


@pytest.mark.asyncio
async def test_delete_portfolio_cascades_runs(sample_portfolio):
    """Test that deleting portfolio also deletes associated runs"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create portfolio and execute run
        create_response = await client.post("/portfolios", json={"portfolio": sample_portfolio})
        portfolio_id = create_response.json()["portfolio_id"]
        
        execute_response = await client.post("/runs/execute", json={"portfolio_id": portfolio_id})
        run_id = execute_response.json()["run_id"]
        
        # Delete portfolio
        await client.delete(f"/portfolios/{portfolio_id}")
        
        # Verify run is also deleted
        get_run_response = await client.get(f"/runs/{run_id}")
        assert get_run_response.status_code == 404

