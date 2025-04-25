import numpy as np
from typing import Optional

from market_sim.models.base_model import BaseModel


class GBMModel(BaseModel):
    """Geometric Brownian Motion model implementation."""

    def simulate(self, S0: float, T: float, n_steps: int, paths: int = 1,
                seed: Optional[int] = None) -> np.ndarray:
        """
        Simulate price paths using Geometric Brownian Motion.
        
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
        self._validate_parameters(S0, T, n_steps, paths)
        
        if seed is not None:
            np.random.seed(seed)
        
        dt = T / n_steps
        drift = self.config.default_drift
        vol = self.config.default_volatility
        
        # Generate random normal variables
        Z = np.random.normal(size=(paths, n_steps))
        
        # Initialize price paths array
        S = np.zeros((paths, n_steps + 1))
        S[:, 0] = S0
        
        # Simulate paths using the closed-form solution
        for t in range(n_steps):
            S[:, t + 1] = S[:, t] * np.exp(
                (drift - 0.5 * vol**2) * dt + vol * np.sqrt(dt) * Z[:, t]
            )
        
        return S