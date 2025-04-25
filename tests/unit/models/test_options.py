import numpy as np
import pytest
from datetime import datetime, timedelta

from market_sim.models.options import (
    BlackScholesModel,
    generate_option_chain,
    OptionType,
    OptionChain
)

def test_black_scholes_call_price():
    """Test Black-Scholes call option pricing."""
    model = BlackScholesModel()
    
    # Known values for verification
    S = 100.0  # Spot price
    K = 100.0  # Strike price
    T = 1.0    # Time to expiry (1 year)
    r = 0.05   # Risk-free rate
    sigma = 0.2  # Volatility
    
    call_price = model.price_option(
        S=S, K=K, T=T, r=r, sigma=sigma, option_type=OptionType.CALL
    )
    
    # Value should be close to theoretical value
    expected_value = 10.45
    assert abs(call_price - expected_value) < 0.1

def test_black_scholes_put_price():
    """Test Black-Scholes put option pricing."""
    model = BlackScholesModel()
    
    S = 100.0
    K = 100.0
    T = 1.0
    r = 0.05
    sigma = 0.2
    
    put_price = model.price_option(
        S=S, K=K, T=T, r=r, sigma=sigma, option_type=OptionType.PUT
    )
    
    # Value should be close to theoretical value
    expected_value = 5.57
    assert abs(put_price - expected_value) < 0.1

def test_generate_option_chain():
    """Test option chain generation."""
    current_price = 100.0
    strike_range_percent = 10
    num_strikes = 5
    days_to_expiry = 30
    volatility = 0.2
    
    chain = generate_option_chain(
        current_price=current_price,
        strike_range_percent=strike_range_percent,
        num_strikes=num_strikes,
        days_to_expiry=days_to_expiry,
        volatility=volatility
    )
    
    # Verify structure and values
    assert isinstance(chain, OptionChain)
    assert len(chain.strikes) == num_strikes
    assert len(chain.calls) == num_strikes
    assert len(chain.puts) == num_strikes
    
    # Verify strike range
    min_strike = current_price * (1 - strike_range_percent/100)
    max_strike = current_price * (1 + strike_range_percent/100)
    assert chain.strikes[0] >= min_strike
    assert chain.strikes[-1] <= max_strike
    
    # Verify option prices are reasonable
    assert all(call > 0 for call in chain.calls)
    assert all(put > 0 for put in chain.puts)

def test_invalid_parameters():
    """Test parameter validation."""
    model = BlackScholesModel()
    
    with pytest.raises(ValueError):
        model.price_option(S=-100, K=100, T=1, r=0.05, sigma=0.2, option_type=OptionType.CALL)
    
    with pytest.raises(ValueError):
        model.price_option(S=100, K=-100, T=1, r=0.05, sigma=0.2, option_type=OptionType.CALL)
    
    with pytest.raises(ValueError):
        model.price_option(S=100, K=100, T=-1, r=0.05, sigma=0.2, option_type=OptionType.CALL)
    
    with pytest.raises(ValueError):
        model.price_option(S=100, K=100, T=1, r=0.05, sigma=-0.2, option_type=OptionType.CALL)