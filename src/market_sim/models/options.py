from dataclasses import dataclass
from enum import Enum
from typing import List
import numpy as np
from scipy.stats import norm


class OptionType(str, Enum):
    CALL = "CALL"
    PUT = "PUT"


@dataclass
class OptionChain:
    """Container for option chain data."""
    strikes: List[float]
    calls: List[float]
    puts: List[float]
    expiry_days: int


class BlackScholesModel:
    """Black-Scholes option pricing model implementation."""
    
    def _validate_parameters(self, S: float, K: float, T: float, sigma: float):
        """Validate option pricing parameters."""
        if S <= 0:
            raise ValueError("Spot price must be positive")
        if K <= 0:
            raise ValueError("Strike price must be positive")
        if T <= 0:
            raise ValueError("Time to expiry must be positive")
        if sigma <= 0:
            raise ValueError("Volatility must be positive")
    
    def price_option(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: OptionType
    ) -> float:
        """
        Calculate option price using Black-Scholes formula.
        
        Parameters:
        -----------
        S : float
            Current stock price
        K : float
            Strike price
        T : float
            Time to expiry in years
        r : float
            Risk-free interest rate
        sigma : float
            Volatility
        option_type : OptionType
            Type of option (CALL or PUT)
            
        Returns:
        --------
        float
            Option price
        """
        self._validate_parameters(S, K, T, sigma)
        
        # Calculate d1 and d2
        d1 = (np.log(S/K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if option_type == OptionType.CALL:
            price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:  # PUT
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
            
        return float(price)


def generate_option_chain(
    current_price: float,
    strike_range_percent: float,
    num_strikes: int,
    days_to_expiry: int,
    volatility: float,
    risk_free_rate: float = 0.05
) -> OptionChain:
    """
    Generate option chain for given parameters.
    
    Parameters:
    -----------
    current_price : float
        Current price of the underlying
    strike_range_percent : float
        Percentage range around current price for strikes
    num_strikes : int
        Number of strike prices to generate
    days_to_expiry : int
        Days until expiration
    volatility : float
        Volatility parameter
    risk_free_rate : float, optional
        Risk-free interest rate (default: 0.05)
        
    Returns:
    --------
    OptionChain
        Generated option chain data
    """
    # Generate strike prices
    strike_min = current_price * (1 - strike_range_percent/100)
    strike_max = current_price * (1 + strike_range_percent/100)
    strikes = np.linspace(strike_min, strike_max, num_strikes)
    
    # Convert days to years
    T = days_to_expiry / 365.0
    
    # Initialize pricing model
    model = BlackScholesModel()
    
    # Calculate option prices for each strike
    calls = []
    puts = []
    for K in strikes:
        call_price = model.price_option(
            S=current_price,
            K=K,
            T=T,
            r=risk_free_rate,
            sigma=volatility,
            option_type=OptionType.CALL
        )
        put_price = model.price_option(
            S=current_price,
            K=K,
            T=T,
            r=risk_free_rate,
            sigma=volatility,
            option_type=OptionType.PUT
        )
        calls.append(call_price)
        puts.append(put_price)
    
    return OptionChain(
        strikes=strikes.tolist(),
        calls=calls,
        puts=puts,
        expiry_days=days_to_expiry
    )