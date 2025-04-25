import uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from market_sim.api.schemas import (
    MarketSimulationRequest,
    SimulationResponse,
    SimulationStatus
)
from market_sim.api.simulation_service import SimulationService

app = FastAPI(
    title="Market Data Simulation API",
    description="API for simulating market data including index and options",
    version="1.0.0"
)

simulation_service = SimulationService()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/api/v1/simulate", response_model=SimulationResponse)
async def simulate_market(request: MarketSimulationRequest):
    """
    Simulate market data based on provided parameters.
    Generates index data and optionally options chain data.
    """
    simulation_id = str(uuid.uuid4())
    try:
        storage_path = await simulation_service.start_simulation(
            simulation_id=simulation_id,
            params=request
        )
        return SimulationResponse(
            simulation_id=simulation_id,
            status="success",
            storage_path=storage_path
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/simulate/{simulation_id}/status", response_model=SimulationStatus)
async def get_simulation_status(simulation_id: str):
    """Get the status of a specific simulation"""
    status = simulation_service.get_status(simulation_id)
    if status is None:
        raise HTTPException(
            status_code=404,
            detail=f"Simulation {simulation_id} not found"
        )
    return status