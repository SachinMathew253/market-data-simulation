import uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from src.market_sim.api.schemas import (
    MarketSimulationRequest,
    SimulationResponse,
    SimulationStatus,
    MarkovJumpSimulationRequest
)
from src.market_sim.api.simulation_service import SimulationService

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

@app.post("/api/v1/simulate/market_data", response_model=SimulationResponse)
async def simulate_market_data(request: MarkovJumpSimulationRequest):
    """Simulates market data based on provided parameters"""
    simulation_id = str(uuid.uuid4())
    try:
        storage_path = await simulation_service.start_market_data_simulation(
            simulation_id=simulation_id,
            params=request
        )
        # model = create_model(params.market_type)
        
        # # Set up default drift values if not provided
        # if params.drift is None:
        #     if params.market_type == MarketType.BULLISH:
        #         params.drift = 0.10
        #     elif params.market_type == MarketType.BEARISH:
        #         params.drift = -0.10
        #     else:
        #         params.drift = 0
                
        # # Run simulation until valid price series found
        # for _ in range(3):
        #     prices = self._run_single_simulation(model, params.initial_value, params.drift, 
        #                                        params.volatility, params.days)
        #     if self._validate_single_simulation_data(prices, params.market_type):
        #         data_frame = pd.DataFrame({
        #             "date": pd.date_range(date.today(), periods=params.days),
        #             "price": prices
        #         })
                
        #         return SimulationResponse(data=data_frame.to_dict("records"))
            
        # If after 3 attempts still no valid series found
        raise HTTPException(status_code=500, detail="Could not generate valid simulation data with given parameters")
        
    except Exception as e:
        return JSONResponse(
            status_code=422,
            content={"message": str(e)}
        )