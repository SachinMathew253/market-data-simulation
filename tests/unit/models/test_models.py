import numpy as np
import pytest

from market_sim.models.base_model import BaseModel
from market_sim.models.gbm_model import GBMModel
from market_sim.models.jump_diffusion_model import JumpDiffusionModel
from market_sim.config.config_manager import ConfigManager


@pytest.fixture
def config():
    """Create test configuration."""
    import os
    os.environ.update({
        'STORAGE_TYPE': 'local',
        'LOCAL_STORAGE_PATH': './test_data',
        'DEFAULT_DRIFT': '0.05',
        'DEFAULT_VOLATILITY': '0.2',
        'DEFAULT_JUMP_INTENSITY': '1.0',
        'DEFAULT_JUMP_MEAN': '0.0',
        'DEFAULT_JUMP_VOLATILITY': '0.2'
    })
    return ConfigManager()

def test_gbm_model_simulation(config):
    """Test GBM model simulation."""
    model = GBMModel(config)
    S0 = 100.0
    T = 1.0
    n_steps = 252
    paths = 1000
    
    # Simulate multiple paths
    simulated_paths = model.simulate(S0, T, n_steps, paths)
    
    # Check shape
    assert simulated_paths.shape == (paths, n_steps + 1)
    
    # Check initial values
    np.testing.assert_array_equal(simulated_paths[:, 0], S0)
    
    # Check that values are positive
    assert np.all(simulated_paths > 0)
    
    # Check statistical properties (approximate)
    final_values = simulated_paths[:, -1]
    log_returns = np.log(final_values / S0)
    
    # Calculate empirical drift and volatility
    emp_drift = np.mean(log_returns) / T
    emp_vol = np.std(log_returns) / np.sqrt(T)
    
    # Check if empirical values are within reasonable bounds
    assert abs(emp_drift - config.default_drift) < 0.1
    assert abs(emp_vol - config.default_volatility) < 0.1

def test_jump_diffusion_model_simulation(config):
    """Test Jump-Diffusion model simulation."""
    model = JumpDiffusionModel(config)
    S0 = 100.0
    T = 1.0
    n_steps = 252
    paths = 1000
    
    # Simulate multiple paths
    simulated_paths = model.simulate(S0, T, n_steps, paths)
    
    # Basic checks
    assert simulated_paths.shape == (paths, n_steps + 1)
    assert np.all(simulated_paths > 0)
    np.testing.assert_array_equal(simulated_paths[:, 0], S0)
    
    # Check for jumps
    daily_returns = np.diff(simulated_paths) / simulated_paths[:, :-1]
    large_moves = np.abs(daily_returns) > 3 * config.default_volatility / np.sqrt(252)
    
    # There should be some large moves due to jumps
    assert np.any(large_moves)

def test_invalid_parameters():
    """Test model behavior with invalid parameters."""
    import os
    os.environ.update({
        'STORAGE_TYPE': 'local',
        'LOCAL_STORAGE_PATH': './test_data',
        'DEFAULT_DRIFT': '-2.0',  # Invalid drift
        'DEFAULT_VOLATILITY': '-0.2',  # Invalid volatility
    })
    
    with pytest.raises(ValueError):
        ConfigManager()

def test_model_validation():
    """Test model parameter validation."""
    model = GBMModel(config)
    
    with pytest.raises(ValueError):
        model.simulate(S0=-100.0, T=1.0, n_steps=252, paths=100)
    
    with pytest.raises(ValueError):
        model.simulate(S0=100.0, T=-1.0, n_steps=252, paths=100)
    
    with pytest.raises(ValueError):
        model.simulate(S0=100.0, T=1.0, n_steps=-252, paths=100)
    
    with pytest.raises(ValueError):
        model.simulate(S0=100.0, T=1.0, n_steps=252, paths=-100)