from abc import ABC, abstractmethod
from typing import Optional

import numpy as np
from market_sim.config.config_manager import ConfigManager


class BaseModel(ABC):
    """Base class for all market simulation models."""

    def __init__(self, config: ConfigManager):
        """Initialize model with configuration."""
        self.config = config

    @abstractmethod
    def simulate(self, S0: float, T: float, n_steps: int, paths: int = 1,
                seed: Optional[int] = None) -> np.ndarray:
        """
        Simulate price paths.
        
        Parameters:
        -----------
        S0 : float
            Initial price
        T : float
            Time horizon in years
        n_steps : int
            Number of time steps
        paths : int, optional
            Number of paths to simulate (default: 1)
        seed : int, optional
            Random seed for reproducibility
            
        Returns:
        --------
        np.ndarray
            Array of shape (paths, n_steps + 1) containing simulated prices
        """
        pass

    def _validate_parameters(self, S0: float, T: float, n_steps: int, paths: int):
        """Validate simulation parameters."""
        if S0 <= 0:
            raise ValueError("Initial price (S0) must be positive")
        if T <= 0:
            raise ValueError("Time horizon (T) must be positive")
        if n_steps <= 0:
            raise ValueError("Number of steps must be positive")
        if paths <= 0:
            raise ValueError("Number of paths must be positive")