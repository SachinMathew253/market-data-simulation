import numpy as np
from typing import Optional

from market_sim.models.base_model import BaseModel


class JumpDiffusionModel(BaseModel):
    """Merton Jump-Diffusion model implementation."""

    def simulate(self, S0: float, T: float, n_steps: int, paths: int = 1,
                seed: Optional[int] = None) -> np.ndarray:
        """
        Simulate price paths using Merton Jump-Diffusion model.
        
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
        lambda_j = self.config.default_jump_intensity
        mu_j = self.config.default_jump_mean
        sigma_j = self.config.default_jump_volatility
        
        # Initialize arrays
        S = np.zeros((paths, n_steps + 1))
        S[:, 0] = S0
        
        # Generate random variables for diffusion
        Z = np.random.normal(size=(paths, n_steps))
        
        # Generate Poisson random variables for jump times
        N = np.random.poisson(lambda_j * dt, size=(paths, n_steps))
        
        # Generate random variables for jump sizes
        Y = np.random.normal(mu_j, sigma_j, size=(paths, n_steps))
        
        # Simulate paths
        for t in range(n_steps):
            # Diffusion component
            diffusion = (drift - 0.5 * vol**2) * dt + vol * np.sqrt(dt) * Z[:, t]
            
            # Jump component
            jumps = N[:, t] * Y[:, t]
            
            # Combine diffusion and jumps
            S[:, t + 1] = S[:, t] * np.exp(diffusion + jumps)
        
        return S