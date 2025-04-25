## Simulate Market Data

## Market Patterns

1. **Trend Patterns:**  
   * Uptrend   
   * Downtrend  
   * Sideways/Range-bound  
   * Volatile/Choppy market  
2. **Reversal**  
3. **Gap Ups / Downs**  
4. **Market Regimes**  
   * Trending vs. Non-trending  
   * High Volatility vs. Low Volatility

## Diff ways to Simulate Market Data

1. Mathematical Model–Based Simulation  
   1. Pros  
      \- Simple and Interpretable / Easier to interpret  
      \- Computational Efficiency / Less resource-intensive compared to training a machine learning model.  
      \- Control / Can directly adjust parameters (drift, volatility, jump intensity, etc.) to simulate specific market conditions (bullish, bearish, volatile, etc.) without the need for large amounts of data  
   2. Cons  
      \- Limited Complexity / While they capture many important market features, these models may not fully account for all non-linearities or complex dependencies present in real markets  
      \- Assumptions / They rely on assumptions (e.g., log-normal returns, constant parameters over short periods)  
2. Machine Learning–Based Simulation  
   1. Pros  
      \- Flexibility / GANs, VAEs, or sequence models such as LSTMs / learn complex, non-linear dynamics from historical data  
      \- Data-Driven / having rich historical data, then ML can potentially capture nuances (e.g., regime shifts, volatility clustering, tail events) that simple mathematical models might miss  
   2. Cons  
      \- Over Engineering Risk / For many simulation tasks, a mathematical model can do the job without the extra complexity and computational cost of ML.  
      \- Calibration and Overfitting / Complexity & Maintenance

"In summary, for many simulation tasks in finance, mathematical models work well and are often preferred for their transparency and efficiency. Machine learning should be considered if the added complexity is justified by your objectives and data availability."

## Mathematical Model–Based Simulation

1. Index Data Simulation  
2. Options Data Simulation

## Index Data Simulation

1. Geometric Brownian Motion (GBM)  
   GBM is one of the simplest models for asset price dynamics:  
   dS/S = μ dt + σdWt
   Where:
      dS/S is the relative change in the stock price.
      μ is the drift rate.
      σ is the volatility.
      dt is the time increment.
      dWt is a Wiener process (Brownian motion) increment.

   \- **Incorporating Bullish/Bearish Conditions**  
     Drift (𝜇) Adjustment:  
   	Bullish Market: Set 𝜇 to a positive value.  
   	Bearish Market: Set 𝜇 to a negative value.

   ```
   ## Code Snippet
   import numpy as np

   def simulate_gbm(S0, mu0, sigma, theta, T, dt, market_type='bullish'):
      # Number of time steps
      N = int(T/dt)
      prices = np.zeros(N+1)
      prices[0] = S0
      
      # Adjust drift based on market type and intensity parameter theta
      if market_type == 'bullish':
         mu = mu0 * (1 + theta)
      elif market_type == 'bearish':
         mu = -abs(mu0) * (1 + theta)  # Ensure drift is negative
      else:
         mu = mu0  # Neutral or baseline
      
      for t in range(1, N+1):
         Z = np.random.normal()
         prices[t] = prices[t-1] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z)
      
      return prices

   # Parameters
   S0 = 100           # Initial index value
   mu0 = 0.05         # Baseline drift (annualized)
   sigma = 0.2        # Volatility (annualized)
   theta = 0.5        # Intensity parameter
   T = 1.0            # 1 year
   dt = 1/252         # Daily steps (assuming 252 trading days)

   # Simulate bullish market
   bullish_prices = simulate_gbm(S0, mu0, sigma, theta, T, dt, market_type='bullish')

   # Simulate bearish market
   bearish_prices = simulate_gbm(S0, mu0, sigma, theta, T, dt, market_type='bearish')
   ```

2. Incorporating Jumps and Regime-Switching  
   1. Jump-Diffusion Models (e.g., Merton's Model)
      dS_t=\mu*S_t*dt+\sigma*S_t*dW_t
      Where dJ  represents the jump component.

      \- **Bullish/Bearish Jumps**  
      In a **bullish market**, you might simulate jumps that predominantly move upward.  
      In a **bearish market**, simulate jumps that are more likely to be downward.  
      \- **Intensity of Jumps**  
      introduce an intensity parameter 𝜆 (jump frequency) and a jump size distribution that can be adjusted to reflect stronger or milder jumps  
        
   2. Regime-Switching Models  
      A common way to simulate different market conditions is to use a regime-switching model, where the market alternates between states (e.g., bullish, bearish, or neutral) according to a probabilistic rule.

   ```
   ## Code Snippet
   import numpy as np

   def simulate_market(S0, regimes, transition_matrix, T, dt,
                     lambda_jump, mu_jump, sigma_jump):
      """
      Simulate OHLC market data with drift adjustments, jumps, and regime switching.
      """
      N = int(T / dt)
      opens = np.zeros(N + 1)
      highs = np.zeros(N + 1)
      lows = np.zeros(N + 1)
      closes = np.zeros(N + 1)
      regime_history = np.zeros(N + 1, dtype=int)
      
      # Initialize first values
      opens[0] = S0
      closes[0] = S0
      highs[0] = S0
      lows[0] = S0
      regime_history[0] = 0  # Start with first regime
      
      current_regime = 0
      
      for t in range(1, N + 1):
         # Regime switching
         current_regime = np.random.choice(len(regimes), p=transition_matrix[current_regime])
         regime_history[t] = current_regime
                # Get current regime parameters
         regime = regimes[current_regime]
         theta = regime.get('theta', 0)
         mu = regime['mu'] * (1 + theta)
         sigma = regime['sigma']
         
         # Open is previous close
         opens[t] = closes[t-1]
         
         # Simulate intra-day price path
         sub_dt = dt / intraday_steps
         current_price = opens[t]
         intra_prices = [current_price]
         
         for _ in range(intraday_steps):
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
         
         # Calculate high and low from intraday path
         day_high = max(intra_prices)
         day_low = min(intra_prices)
         highs[t] = max(day_high, closes[t])
         lows[t] = min(day_low, closes[t])
    
      return opens, highs, lows, closes, regime_history

   # Example usage
   S0 = 100
   regimes = [
      {'name': 'Bullish', 'mu': 0.08, 'sigma': 0.15, 'theta': 0.5},
      {'name': 'Bearish', 'mu': -0.05, 'sigma': 0.25, 'theta': 0.0}
   ]
   transition_matrix = np.array([[0.9, 0.1], [0.2, 0.8]])
   T = 1.0
   dt = 1/252
   lambda_jump = 1.0
   mu_jump = 0.0
   sigma_jump = 0.2

   # Run simulation with 24 intra-day steps (e.g., hourly for a 24-hour market)
   opens, highs, lows, closes, regime_history = simulate_market(
      S0, regimes, transition_matrix, T, dt,
      lambda_jump, mu_jump, sigma_jump)
   ```