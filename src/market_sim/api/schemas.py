from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class MarketType(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    VOLATILE = "VOLATILE"
    RANGE_BOUND = "RANGE_BOUND"


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


class SimulationStatus(BaseModel):
    simulation_id: str
    status: str
    progress: Optional[float] = None
    error_message: Optional[str] = None
    storage_path: Optional[str] = None