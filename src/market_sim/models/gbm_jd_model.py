import numpy as np
from typing import Optional

from market_sim.models.base_model import BaseModel
import pandas as pd
from scipy.stats import norm
from py_vollib.black_scholes_merton.greeks.analytical import delta
from datetime import time, datetime, timedelta


class GBM_JD_Model(BaseModel):
    """Geometric Brownian Motion model implementation."""

    def _get_next_expiry(self, dt):
        # Thursday corresponds to weekday 3 (Monday is 0)
        days_ahead = (3 - dt.weekday()) % 7
        # If today is Thursday, move to next Thursday (7 days later)
        if days_ahead == 0:
            days_ahead = 7
        return (dt + timedelta(days=days_ahead)).date()

    def _get_adjusted_sigma(self, base_sigma, previous_close, previous_sma):
        # Use small random factor when price is far from SMA, else large volatility
        v_small = np.random.normal(0, 1)
        v_large = np.random.normal(0, 3)
        w = 0.01

        if previous_sma is not np.nan and abs(previous_close - previous_sma) / previous_close < 0.001:
            return base_sigma * (1 + (w * v_large))
        return base_sigma * (1 + (w * v_small))

    def _black_scholes_price(self, S, K, T, r, sigma, option):
        d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        if option == 'call':
            price = S * norm.cdf(d1) - K * np.exp(-r*T) * norm.cdf(d2)
        else:  # put
            price = K * np.exp(-r*T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        return np.round(price, decimals=3)
    
    def _simulate_options_chain(self, timestamp, spot_price, strikes, sigma):
        expiry_date = self._get_next_expiry(dt=timestamp)
        tte=((datetime.combine(expiry_date, time(15, 29))-timestamp).total_seconds())/(365*24*60*60)
        options_chain = []
        for strike in strikes:
            options_chain.append({
                "DateTime": timestamp,
                "Strike": strike,
                "StrikeType": "CE",
                "Close": self._black_scholes_price(
                    S=spot_price,
                    K=strike,
                    r=0.065,
                    T=tte,
                    sigma=sigma,
                    option="call"
                ),
                "Delta": delta(
                    S=spot_price,
                    K=strike,
                    r=0.065,
                    t=tte,
                    sigma=sigma,
                    flag='c',
                    q=0
                ), 
                "Close_index": spot_price,
                "ExpiryDate": expiry_date
            })

            options_chain.append({
                "DateTime": timestamp,
                "Strike": strike,
                "StrikeType": "PE",
                "Close": self._black_scholes_price(
                    S=spot_price,
                    K=strike,
                    r=0.065,
                    T=tte,
                    sigma=sigma,
                    option="put"
                ),
                "Delta": delta(
                    S=spot_price,
                    K=strike,
                    r=0.065,
                    t=tte,
                    sigma=sigma,
                    flag='p',
                    q=0
                ),
                "Close_index": spot_price,
                "ExpiryDate": expiry_date
            })

        return pd.DataFrame(options_chain)

    def _simulate_market(self, S0, regimes, transition_matrix, T, dt,
                    lambda_jump, mu_jump, sigma_jump, steps=1, sma_length=30):
        """
        Simulate OHLC market data with drift adjustments, jumps, and regime switching.

        Parameters:
        -----------
        steps : int
            Number of intra-day steps to simulate for each main time step (dt).
        """
        N = int(T / dt)

        # Minute-frequency index over trading days
        potential_dates = (
            pd.date_range(
                start="2025-01-03 09:15",
                periods=(N+1)*10,
                freq="T"
            )
            .to_series()
            .between_time("09:15", "15:29")
            .loc[lambda s: s.index.weekday < 5]
            .index
        )

        dates = potential_dates[0:N+1]
        opens = np.zeros(N + 1)
        highs = np.zeros(N + 1)
        lows = np.zeros(N + 1)
        closes = np.zeros(N + 1)
        regime_history = np.zeros(N + 1, dtype=int)
        ema = np.full(N + 1, np.nan)
        sigma_history = np.zeros(N + 1)
        
        # Initialize first values
        opens[0] = S0
        closes[0] = S0
        highs[0] = S0
        lows[0] = S0
        regime_history[0] = 0  # Start with first regime
        sigma_history[0] = regimes[regime_history[0]].sigma
        
        current_regime = 0
        
        options_master = pd.DataFrame()
        for t in range(1, N + 1):
            # Regime switching
            current_regime = np.random.choice(len(regimes), p=transition_matrix[current_regime])
            regime_history[t] = current_regime
            
            # Get current regime parameters
            regime = regimes[current_regime]
            theta = regime.theta
            mu = regime.mu * (1 + theta)
            sigma = self._get_adjusted_sigma(
                base_sigma=regime.sigma,
                previous_close=closes[t-1],
                previous_sma=ema[t-1]
            )
            sigma_history[t] = sigma

            # Open is previous close
            opens[t] = closes[t-1]
            
            # Simulate intra-day price path
            sub_dt = dt / steps
            current_price = opens[t]
            intra_prices = [current_price]
            
            for _ in range(steps):
                Z = np.random.normal()
                drift = (mu - 0.5 * sigma**2) * sub_dt
                vol = sigma * np.sqrt(sub_dt) * Z
                current_price *= np.exp(drift + vol)
                intra_prices.append(current_price)
            
            pre_jump_close = current_price
            
            # Check for jump event
            if np.random.uniform() < lambda_jump * dt:
                jump_multiplier = np.exp(np.random.normal(mu_jump, sigma_jump))
                closes[t] = pre_jump_close * jump_multiplier
            else:
                closes[t] = pre_jump_close
            
            # Calculate high and low including jump effect
            day_high = max(intra_prices)
            day_low = min(intra_prices)
            highs[t] = max(day_high, closes[t])
            lows[t] = min(day_low, closes[t])

            if t >= sma_length :
                closes_ema = pd.Series(closes).ewm(span=sma_length, adjust=False).mean().to_numpy()
                ema[t] = closes_ema[t-1]
            
            ## Generating Options Chain
            # — new 50-point grid for 50 strikes —
            center = int(np.round(closes[t] / 50) * 50)     # round spot to nearest 50 :contentReference[oaicite:3]{index=3}
            half = 25
            offsets = np.arange(-half, half, 1) * 50  # 50-point steps :contentReference[oaicite:4]{index=4}
            strikes = np.sort(center + offsets).tolist()

            options_chain = self._simulate_options_chain(
                timestamp=dates[t],
                spot_price=closes[t],
                strikes=strikes,
                sigma=sigma
            )
            options_master = pd.concat([options_master, options_chain], ignore_index=True)

        index_master = pd.DataFrame({
            'DateTime': dates,
            'Open': opens,
            'High': highs,
            'Low': lows,
            'Close': closes,
            'Regime History': regime_history,
            'Sigma History': sigma_history,
            'Close_EMA': ema})
        return index_master, options_master

    def simulate(self, params: type) -> np.ndarray:
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
        # self._validate_parameters(S0, T, n_steps, paths)
        index, options = self._simulate_market(
            S0=params.initial_value,
            regimes=params.regimes,
            transition_matrix=params.transition_matrix, 
            T=params.time_period_days/252, 
            dt=1.0 / (252 * 375),
            lambda_jump=params.lambda_jump, 
            mu_jump=params.mu_jump, 
            sigma_jump=params.sigma_jump, 
            steps=params.steps
        )
        return index, options        