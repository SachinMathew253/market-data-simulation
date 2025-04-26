from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, model_validator, conlist


class MarketType(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    VOLATILE = "VOLATILE"
    RANGE_BOUND = "RANGE_BOUND"
    GBM = "GBM"


class StorageType(str, Enum):
    LOCAL = "LOCAL"
    GCS = "GCS"


class OptionsConfig(BaseModel):
    strike_range_percent: float = Field(
        default=10.0,
        gt=0,
        description="Percentage range around current price for strike prices"
    )
    num_strikes: int = Field(
        default=10,
        gt=0,
        description="Number of strike prices to generate"
    )
    time_to_expiry_days: int = Field(
        default=30,
        gt=0,
        description="Days to expiry for options"
    )


class MarketSimulationRequest(BaseModel):
    initial_value: float = Field(
        ...,
        gt=0,
        description="Initial value of the index"
    )
    market_type: MarketType = Field(
        ...,
        description="Type of market behavior to simulate"
    )
    volatility: float = Field(
        ...,
        gt=0,
        le=1,
        description="Volatility parameter for the simulation"
    )
    time_period_days: int = Field(
        ...,
        gt=0,
        description="Number of days to simulate"
    )
    include_options: bool = Field(
        default=False,
        description="Whether to generate option chain data"
    )
    storage_type: StorageType = Field(
        ...,
        description="Storage type for simulation results"
    )
    output_path: str = Field(
        ...,
        min_length=1,
        description="Path where simulation results will be stored"
    )
    options_config: Optional[OptionsConfig] = Field(
        default=None,
        description="Configuration for options generation"
    )


class SimulationResponse(BaseModel):
    simulation_id: str = Field(
        ...,
        description="Unique identifier for the simulation"
    )
    status: str = Field(
        ...,
        description="Status of the simulation"
    )
    storage_path: str = Field(
        ...,
        description="Path where simulation results are stored"
    )

class SimulateMarketDataResponse(BaseModel):
    simulation_id: str = Field(
        ...,
        description="Unique identifier for the simulation"
    )
    status: str = Field(
        ...,
        description="Status of the simulation"
    )
    index_csv: Optional[list] = Field(
        default=None,
        description="Path where simulated Index results are stored"
    )
    options_csv: Optional[list] = Field(
        default=None,
        description="Path where simulated Options results are stored"
    )


class SimulationStatus(BaseModel):
    simulation_id: str
    status: str
    progress: Optional[float] = None
    error_message: Optional[str] = None
    storage_path: Optional[str] = None



class Regime(BaseModel):
    name: str = Field(..., min_length=1)
    mu: float = Field(...)
    sigma: float = Field(..., gt=0)
    theta: float = Field(...)

class MarkovJumpSimulationRequest(BaseModel):
    initial_value: float = Field(..., gt=0)
    time_period_days: int = Field(..., gt=0)
    storage_type: str = Field(...)
    output_path: str = Field(..., min_length=1)

    transition_matrix: list[conlist(float, min_length=1)] = Field(...)
    regimes: list[Regime] = Field(...)
    steps: int = Field(..., gt=0)
    lambda_jump: float = Field(..., gt=0)
    mu_jump: float = Field(...)
    sigma_jump: float = Field(..., gt=0)

    @model_validator(mode="after")
    def check_matrix_and_regimes(cls, m: "MarkovJumpSimulationRequest"):
        matrix = m.transition_matrix
        regimes = m.regimes
        n = len(matrix)
        if any(len(row) != n for row in matrix):
            raise ValueError("transition_matrix must be square (n × n)")
        for i, row in enumerate(matrix):
            if abs(sum(row) - 1.0) > 1e-6:
                raise ValueError(f"Row {i} must sum to 1")
        if len(regimes) != n:
            raise ValueError("Number of regimes must equal matrix dimension")
        return m
