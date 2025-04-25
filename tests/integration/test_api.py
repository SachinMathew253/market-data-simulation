import os
from pathlib import Path
import json
import shutil
from fastapi.testclient import TestClient
import pytest
from dotenv import load_dotenv
import pandas as pd
import numpy as np

# Load test environment variables
test_env_path = Path(__file__).parent.parent / '.env.test'
load_dotenv(test_env_path)

from market_sim.api.app import app
from market_sim.api.schemas import (
    MarketSimulationRequest,
    MarketType,
    StorageType,
    SimulationResponse
)

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_env():
    """Create test data directory if it doesn't exist"""
    test_data_path = Path(os.getenv('LOCAL_STORAGE_PATH'))
    test_data_path.mkdir(parents=True, exist_ok=True)
    yield
    # Cleanup test files after tests
    if test_data_path.exists():
        shutil.rmtree(test_data_path)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_simulate_market_index():
    request_data = {
        "initial_value": 18000,
        "market_type": "BULLISH",
        "volatility": 0.2,
        "time_period_days": 252,
        "include_options": False,
        "storage_type": "LOCAL",
        "output_path": "test_simulation.pkl"
    }
    
    response = client.post("/api/v1/simulate", json=request_data)
    assert response.status_code == 200
    result = response.json()
    assert "simulation_id" in result
    assert "storage_path" in result
    assert result["status"] == "success"

def test_simulate_market_with_options():
    request_data = {
        "initial_value": 18000,
        "market_type": "BULLISH",
        "volatility": 0.2,
        "time_period_days": 252,
        "include_options": True,
        "storage_type": "LOCAL",
        "output_path": "test_simulation_with_options.pkl",
        "options_config": {
            "strike_range_percent": 10,
            "num_strikes": 10,
            "time_to_expiry_days": 30
        }
    }
    
    response = client.post("/api/v1/simulate", json=request_data)
    assert response.status_code == 200
    result = response.json()
    assert "simulation_id" in result
    assert "storage_path" in result
    assert result["status"] == "success"

def test_invalid_market_type():
    request_data = {
        "initial_value": 18000,
        "market_type": "INVALID",  # Invalid market type
        "volatility": 0.2,
        "time_period_days": 252,
        "include_options": False,
        "storage_type": "LOCAL",
        "output_path": "test_simulation.pkl"
    }
    
    response = client.post("/api/v1/simulate", json=request_data)
    assert response.status_code == 422

def test_get_simulation_status():
    # First create a simulation
    request_data = {
        "initial_value": 18000,
        "market_type": "BULLISH",
        "volatility": 0.2,
        "time_period_days": 252,
        "include_options": False,
        "storage_type": "LOCAL",
        "output_path": "status_test.pkl"
    }
    
    response = client.post("/api/v1/simulate", json=request_data)
    assert response.status_code == 200
    simulation_id = response.json()["simulation_id"]
    
    # Then check its status
    status_response = client.get(f"/api/v1/simulate/{simulation_id}/status")
    assert status_response.status_code == 200
    assert "status" in status_response.json()

def test_invalid_simulation_id():
    response = client.get("/api/v1/simulate/invalid-id/status")
    assert response.status_code == 404

def test_invalid_parameters():
    """Test simulation with invalid parameters"""
    params = {
        "initial_value": -1000,  # Invalid negative value
        "market_type": "BULLISH",
        "volatility": 2.0,  # Invalid volatility > 1
        "time_period_days": 0,  # Invalid zero days
        "include_options": False,
        "storage_type": "LOCAL",
        "output_path": "test_simulation.pkl"
    }
    response = client.post("/api/v1/simulate", json=params)
    assert response.status_code == 422  # Validation error