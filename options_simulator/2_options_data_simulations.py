import numpy as np
import pandas as pd

def simulate_paths(S0, T, r, sigma, n_simulations, steps=252):
    """Simulate stock price paths using Geometric Brownian Motion with antithetic variates."""
    dt = T / steps
    # Generate random samples (antithetic included)
    Z = np.random.normal(0, 1, (n_simulations, steps))
    Z = np.concatenate([Z, -Z], axis=0)  # Antithetic paths
    n_paths = Z.shape[0]
    
    # Simulate price paths
    S = np.zeros((n_paths, steps + 1))
    S[:, 0] = S0
    for t in range(1, steps + 1):
        drift = (r - 0.5 * sigma**2) * dt
        diffusion = sigma * np.sqrt(dt) * Z[:, t-1]
        S[:, t] = S[:, t-1] * np.exp(drift + diffusion)
    
    return S[:, -1]  # Return final prices

def compute_prices(ST, K_list, T, r, option_type):
    """Compute option prices for multiple strikes using vectorized operations."""
    K_array = np.array(K_list)
    ST_matrix = ST.reshape(-1, 1)
    
    if option_type == 'call':
        payoffs = np.maximum(ST_matrix - K_array, 0)
    elif option_type == 'put':
        payoffs = np.maximum(K_array - ST_matrix, 0)
    
    prices = np.exp(-r * T) * np.mean(payoffs, axis=0)
    return dict(zip(K_list, prices))

def generate_options_chain(S0, expiries, strikes, r, sigma, n_simulations, steps_per_year=252):
    """Generate complete options chain with call/put prices for multiple expiries and strikes."""
    options_chain = []
    
    for T in expiries:
        steps = int(T * steps_per_year)
        ST = simulate_paths(S0, T, r, sigma, n_simulations, steps)
        
        # Compute prices for all strikes
        call_prices = compute_prices(ST, strikes, T, r, 'call')
        put_prices = compute_prices(ST, strikes, T, r, 'put')
        
        # Store results
        for K in strikes:
            options_chain.append({
                'Expiry': T,
                'Strike': K,
                'Call': call_prices[K],
                'Put': put_prices[K]
            })
    
    return pd.DataFrame(options_chain)

# if __name__ == "__main__":
#     import numpy as np
#     import pandas as pd

#     # Market inputs for 1-week NIFTY 50 options
#     S0 = 24300                    # Spot level :contentReference[oaicite:10]{index=10}
#     r = 0.06                      # Risk-free rate 6% p.a. :contentReference[oaicite:11]{index=11}
#     sigma = 0.196                 # 19.6% annual vol :contentReference[oaicite:12]{index=12}
#     n_simulations = 10000         # Monte Carlo paths (×2 antithetic)
#     steps_per_year = 252          # daily steps
#     T = 1/52                      # 1-week expiry (years) :contentReference[oaicite:13]{index=13}

#     # Generate strikes ATM ±5% in 50-point intervals :contentReference[oaicite:14]{index=14}
#     strikes = list(np.arange(
#         round(S0*0.95/50)*50,
#         round(S0*1.05/50)*50 + 1,
#         50
#     ))

#     expiries = [T]  # only 1-week

#     # Call your existing function
#     options_df = generate_options_chain(
#         S0,
#         expiries,
#         strikes,
#         r,
#         sigma,
#         n_simulations,
#         steps_per_year
#     )

#     print("1-Week NIFTY 50 Options Chain:")
#     print(options_df)


if __name__ == "__main__":
    import numpy as np
    import pandas as pd

    # market inputs unchanged…
    S0 = 17701.7
    r = 0.065
    sigma = 0.196
    n_simulations = 10000
    steps_per_year = 252
    T = 6.25/364

    # — new 50-point grid for 50 strikes —
    center = int(np.round(S0 / 50) * 50)     # round spot to nearest 50 :contentReference[oaicite:3]{index=3}
    half = 25
    offsets = np.arange(-half, half, 1) * 50  # 50-point steps :contentReference[oaicite:4]{index=4}
    strikes = np.sort(center + offsets).tolist()

    expiries = [T]

    options_df = generate_options_chain(
        S0,
        expiries,
        strikes,
        r,
        sigma,
        n_simulations,
        steps_per_year
    )

    print("1-Week NIFTY 50 Options Chain (50 strikes @50-pt):")
    print(options_df)
    print(111223)
