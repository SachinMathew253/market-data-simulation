from typing import Dict, Optional
import asyncio
from datetime import datetime
import numpy as np
import pandas as pd

from market_sim.api.schemas import (
    MarketSimulationRequest,
    SimulationStatus,
    MarketType,
    StorageType,
    MarkovJumpSimulationRequest
)
from market_sim.api.simulate_pcr import simulate_oi_movement
from market_sim.config.config_manager import ConfigManager
from market_sim.models.gbm_model import GBMModel
from market_sim.models.jump_diffusion_model import JumpDiffusionModel
from market_sim.models.gbm_jd_model import GBM_JD_Model
from market_sim.models.options import generate_option_chain
from market_sim.storage.storage_interface import StorageInterface
from market_sim.storage.local_storage import LocalStorage
from market_sim.storage.gcs_storage import GCSStorage


class SimulationService:
    def __init__(self):
        self._simulations: Dict[str, SimulationStatus] = {}
        self._config = ConfigManager()
        
    def _create_model(self, market_type: MarketType):
        """Create appropriate model based on market type"""
        if market_type in [MarketType.VOLATILE]:
            return JumpDiffusionModel(self._config)
        elif market_type in [MarketType.GBM]:
            return GBMModel(self._config)
        return GBM_JD_Model(self._config)
    
    def _get_storage(self, storage_type: StorageType) -> StorageInterface:
        """Get storage implementation based on type"""
        if storage_type == StorageType.GCS:
            return GCSStorage(self._config)
        return LocalStorage(self._config)
    
    def _validate_simulation_data(self, prices: np.ndarray, market_type: MarketType) -> bool:
        """
        Validate the simulated price data based on market type.
        Returns True if validation passes, False otherwise.
        """
        if len(prices) == 0:
            return False
            
        # Check for NaN or infinite values
        if np.any(np.isnan(prices)) or np.any(np.isinf(prices)):
            return False
            
        # Calculate returns
        returns = np.diff(prices) / prices[:-1]
        
        # Market type specific validation
        if market_type == MarketType.BULLISH:
            # For bullish market, expect positive overall return
            total_return = (prices[-1] / prices[0]) - 1
            if total_return <= 0:
                return False
                
        elif market_type == MarketType.BEARISH:
            # For bearish market, expect negative overall return
            total_return = (prices[-1] / prices[0]) - 1
            if total_return >= 0:
                return False
                
        elif market_type == MarketType.RANGE_BOUND:
            # For range-bound, expect limited deviation from initial price
            max_deviation = np.abs(prices - prices[0]).max() / prices[0]
            if max_deviation > 0.2:  # 20% max deviation
                return False
                
        return True
    
    async def start_market_data_simulation(
        self,
        simulation_id: str,
        params: MarkovJumpSimulationRequest
    ) -> tuple[list, list]:
        """
        Start a new market simulation with the given parameters.
        Returns the storage path where results will be saved.
        """
        self._simulations[simulation_id] = SimulationStatus(
            simulation_id=simulation_id,
            status="running",
            progress=0.0
        )
        try:
            # Create model based on market type
            model = self._create_model(market_type="DEFAULT")
            index_data, options_data = model.simulate(
                params=params
            )

            # Add Simulated OI
            try:
                options_data = simulate_oi_movement(index_data, options_data)
            except Exception as e:
                print(f"Error simulating OI movement: {e}")
                raise

            # Store results
            index_data_csv: list = index_data.to_dict(orient='records')
            options_data_csv: list = options_data.to_dict(orient='records')
            # Save index data
            storage = self._get_storage(params.storage_type)
            index_storage_path = f"{simulation_id}_index_data.csv"
            storage.save(index_storage_path, index_data)
            print(f"Index data saved to {index_storage_path}")

            options_storage_path = f"{simulation_id}_options_data.csv"
            storage.save(options_storage_path, options_data)
            print(f"Options data saved to {options_storage_path}")
            
            # Update simulation status
            self._simulations[simulation_id].status = "completed"
            self._simulations[simulation_id].progress = 100.0

            # Return storage path
            return (index_data_csv, options_data_csv)

        except Exception as e:
            self._simulations[simulation_id].status = "failed"
            self._simulations[simulation_id].error_message = str(e)
            raise
    
    async def start_simulation(
        self,
        simulation_id: str,
        params: MarketSimulationRequest
    ) -> str:
        """
        Start a new market simulation with the given parameters.
        Returns the storage path where results will be saved.
        """
        self._simulations[simulation_id] = SimulationStatus(
            simulation_id=simulation_id,
            status="running",
            progress=0.0
        )
        
        try:
            # Create model based on market type
            model = self._create_model(params.market_type)
            
            # Set up initial simulation parameters
            drift = 0.1 if params.market_type == MarketType.BULLISH else -0.1
            if params.market_type == MarketType.RANGE_BOUND:
                drift = 0.0
            vol = params.volatility
            
            # Run simulation with retries if validation fails
            max_attempts = 3
            for attempt in range(max_attempts):
                # Run simulation
                prices = await self._run_simulation(
                    model=model,
                    initial_value=params.initial_value,
                    drift=drift,
                    volatility=vol,
                    days=params.time_period_days,
                    simulation_id=simulation_id
                )
                
                # Validate simulation data
                if self._validate_simulation_data(prices, params.market_type):
                    break
                    
                if attempt == max_attempts - 1:
                    raise ValueError(f"Failed to generate valid {params.market_type} market data after {max_attempts} attempts")
            
            # Create DataFrame with dates
            dates = pd.date_range(
                start=datetime.now(),
                periods=len(prices),
                freq='B'
            )
            result_df = pd.DataFrame({
                'date': dates,
                'price': prices
            })
            
            # Generate options if requested
            if params.include_options and params.options_config:
                self._simulations[simulation_id].status = "generating_options"
                
                # Generate option chain for the final price
                final_price = prices[-1]
                option_chain = generate_option_chain(
                    current_price=final_price,
                    strike_range_percent=params.options_config.strike_range_percent,
                    num_strikes=params.options_config.num_strikes,
                    days_to_expiry=params.options_config.time_to_expiry_days,
                    volatility=vol
                )
                
                # Add option chain data to results
                result_df = pd.concat([
                    result_df,
                    pd.DataFrame({
                        'strike_price': option_chain.strikes,
                        'call_price': option_chain.calls,
                        'put_price': option_chain.puts,
                        'days_to_expiry': option_chain.expiry_days
                    })
                ], axis=1)
            
            # Store results
            storage = self._get_storage(params.storage_type)
            storage_path = params.output_path
            storage.save(storage_path, result_df)
            
            # Update simulation status
            self._simulations[simulation_id].status = "completed"
            self._simulations[simulation_id].progress = 100.0
            
            return storage_path
            
        except Exception as e:
            self._simulations[simulation_id].status = "failed"
            self._simulations[simulation_id].error_message = str(e)
            raise
    
    async def _run_simulation(
        self,
        model,
        initial_value: float,
        drift: float,
        volatility: float,
        days: int,
        simulation_id: str
    ) -> pd.Series:
        """Run the actual simulation with progress updates"""
        prices = model.simulate(
            S0=initial_value,
            T=days/252,  # Convert days to years
            n_steps=days,
            paths=1,
            seed=None
        )[0]  # Take first path
        
        # Update progress
        self._simulations[simulation_id].progress = 100.0
        
        return prices
    
    def get_status(self, simulation_id: str) -> Optional[SimulationStatus]:
        """Get the current status of a simulation"""
        return self._simulations.get(simulation_id)
    