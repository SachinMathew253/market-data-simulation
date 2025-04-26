import pandas as pd
import numpy as np

def add_new_daily_oi(options, index_value, day_date):
    """
    Add new OI for a new trading day.
    
    Args:
        options: DataFrame containing options data
        index_value: Current spot price
        day_date: Current trading date
        
    Returns:
        Updated options DataFrame with new OI added
    """
    # Filter options for the current day
    day_options = options[options['Date'] == day_date]
    if day_options.empty:
        return options
    
    # Get unique expiry dates and process each separately
    for expiry in day_options['ExpiryDate'].unique():
        expiry_options = day_options[day_options['ExpiryDate'] == expiry]
        
        # Calculate days to expiry
        expiry_date = pd.to_datetime(expiry)
        current_date = pd.to_datetime(day_date)
        days_to_expiry = (expiry_date - current_date).days
        
        # Calculate total OI for this expiry
        total_expiry_oi = expiry_options['OI'].sum()
        
        # New OI to add (20% of current total)
        new_oi_total = int(total_expiry_oi * 0.2)
        
        # Determine distance from spot based on days to expiry
        distance = 150 if days_to_expiry <= 3 else 200
        
        # Determine if xx50 strikes should be included
        include_xx50 = days_to_expiry <= 3
        
        # Find eligible target strikes
        ce_targets = []
        pe_targets = []
        
        # Find eligible CE targets (above spot)
        ce_candidates = expiry_options[
            (expiry_options['StrikeType'] == 'CE') & 
            (expiry_options['Strike'] >= index_value + distance)
        ]
        
        # Find eligible PE targets (below spot)
        pe_candidates = expiry_options[
            (expiry_options['StrikeType'] == 'PE') & 
            (expiry_options['Strike'] <= index_value - distance)
        ]
        
        # Filter out xx50 strikes if needed
        if not include_xx50:
            ce_candidates = ce_candidates[ce_candidates['Strike'] % 100 != 50]
            pe_candidates = pe_candidates[pe_candidates['Strike'] % 100 != 50]
        
        # Sort candidates
        ce_candidates = ce_candidates.sort_values('Strike')
        pe_candidates = pe_candidates.sort_values('Strike', ascending=False)
        
        # Take the first 5 eligible strikes for each type
        ce_targets = ce_candidates.head(5)
        pe_targets = pe_candidates.head(5)
        
        if len(ce_targets) > 0 and len(pe_targets) > 0:
            # Distribution weights
            weights = [0.5, 0.2, 0.15, 0.1, 0.05]
            
            # Divide new OI between CE and PE
            ce_oi_to_add = int(new_oi_total / 2)
            pe_oi_to_add = new_oi_total - ce_oi_to_add
            
            # Add OI to CE targets
            for i, (idx, row) in enumerate(ce_targets.iterrows()):
                if i < len(weights):
                    oi_addition = int(ce_oi_to_add * weights[i])
                    options.loc[idx, 'OI'] += oi_addition
            
            # Add OI to PE targets
            for i, (idx, row) in enumerate(pe_targets.iterrows()):
                if i < len(weights):
                    oi_addition = int(pe_oi_to_add * weights[i])
                    options.loc[idx, 'OI'] += oi_addition
    
    return options

def initialize_option_chain_oi(options, index_value, total_oi=(5.9e+10)*2):
    """
    Initialize the OI distribution in an option chain with two distinct normal distributions
    500 points away from spot price.
    """
    # Clear existing OI or create column if it doesn't exist
    if 'OI' not in options.columns:
        options['OI'] = 0
    else:
        options['OI'] = 0
    
    # Process each expiry date separately
    for expiry in options['ExpiryDate'].unique():
        expiry_options = options[options['ExpiryDate'] == expiry]
        
        # Get CE and PE options
        ce_options = expiry_options[expiry_options['StrikeType'] == 'CE']
        pe_options = expiry_options[expiry_options['StrikeType'] == 'PE']
        
        if len(ce_options) == 0 or len(pe_options) == 0:
            continue
        
        # Define peak centers exactly 500 points away from spot
        ce_center = index_value + 150
        pe_center = index_value - 150
        
        # Standard deviation for normal distribution (tighter for clearer peaks)
        std_dev = 100
        
        # Create distributions
        for idx, row in ce_options.iterrows():
            strike = row['Strike']
            # Normal distribution formula with center at ce_center
            distance = abs(strike - ce_center)
            oi_value = np.exp(-0.5 * (distance / std_dev)**2)
            options.loc[idx, 'OI'] = int(oi_value * total_oi * 0.4)  # 40% of total OI for CE
        
        for idx, row in pe_options.iterrows():
            strike = row['Strike']
            # Normal distribution formula with center at pe_center
            distance = abs(strike - pe_center)
            oi_value = np.exp(-0.5 * (distance / std_dev)**2)
            options.loc[idx, 'OI'] = int(oi_value * total_oi * 0.4)  # 40% of total OI for PE
        
        # Scale to ensure total OI matches target
        current_total = options[options['ExpiryDate'] == expiry]['OI'].sum()
        if current_total > 0:
            scaling_factor = total_oi / current_total
            options.loc[options['ExpiryDate'] == expiry, 'OI'] = (options.loc[options['ExpiryDate'] == expiry, 'OI'] * scaling_factor).astype(int)
    
    return options

def calculate_time_based_reallocation_rate(days_to_expiry):
    """
    Calculate OI reallocation rate based on days to expiry:
    - On expiry day (0): 50%
    - 1 day to expiry: 30%
    - 6 days to expiry: 10%
    - Linear interpolation between these points
    """
    if days_to_expiry <= 0:  # Expiry day
        return 0.50
    elif days_to_expiry <= 1:
        return 0.30
    elif days_to_expiry <= 6:
        # Linear interpolation between 10% (6 days) and 30% (1 day)
        return 0.30 - (days_to_expiry - 1) * (0.20 / 5)
    else:
        return 0.10  # More than 6 days

def simulate_oi_movement(index, original_options):
    # Load data
    options = original_options.copy()
    options['Date'] = options['DateTime'].dt.date
    options['Time'] = options['DateTime'].dt.time
    index['Date'] = index['DateTime'].dt.date
    index['Time'] = index['DateTime'].dt.time
    
    # Get the starting spot price from the index data
    start_time = options['DateTime'].min()
    start_index = index[index['DateTime'] <= start_time]
    if start_index.empty:
        print("Warning: No index data found for start time.")
        start_index_value = 24000  # Default value if no data
    else:
        start_index_value = start_index.iloc[-1]['Close']
    
    # Initialize the option chain with proper OI distribution
    print(f"Initializing option chain with OI distribution around spot price {start_index_value}...")
    options = initialize_option_chain_oi(options, start_index_value)

    # Preprocess dates and times
    options['ExpiryDate'] = pd.to_datetime(options['ExpiryDate'], dayfirst=True, format='%Y-%m-%d') + pd.Timedelta(hours=15, minutes=29)
    options['time_to_expiry'] = (options['ExpiryDate'] - options['DateTime']).dt.total_seconds() / 60

    # Sort data
    index.sort_values('DateTime', inplace=True)
    options.sort_values(['ExpiryDate', 'DateTime', 'Strike'], inplace=True)

    # Calculate index price changes
    index['delta_close'] = index['Close'].diff()

    # Merge index data into options (asof merge for timestamps)
    options = pd.merge_asof(options, index[['DateTime', 'Close', 'delta_close']], 
                            on='DateTime', direction='backward', suffixes=('', '_index'))

    print("Data loaded and preprocessed.")
    
    # Process data day by day first to add new OI for each trading day
    unique_dates = sorted(options['Date'].unique())
    print(f"Processing {len(unique_dates)} trading days for new OI additions...")
    
    for day in unique_dates:
        # Get the closing index value for the day
        day_index = index[index['Date'] == day]
        if day_index.empty:
            continue
        
        # Use the last price of the day as spot reference
        day_spot = day_index.iloc[-1]['Close']
        
        # Add new OI for this trading day
        options = add_new_daily_oi(options, day_spot, day)
    
    # Process data minute by minute with enhanced logic
    time_slots = sorted(options['DateTime'].unique())
    print(f"Processing {len(time_slots)} time slots sequentially...")
    
    for current_time in time_slots:
        # Filter data for current time
        current_options = options[options['DateTime'] == current_time].copy()
        current_index = index[index['DateTime'] == current_time]
        
        if current_index.empty:
            continue
        
        # Calculate days to expiry for each option
        current_date = pd.to_datetime(current_time).date()
        current_options['days_to_expiry'] = current_options['ExpiryDate'].dt.date.apply(lambda x: (x - current_date).days)
        
        # Current spot price
        current_spot = current_index['Close'].values[0]
        
        # Process each expiry separately
        for expiry in current_options['ExpiryDate'].unique():
            expiry_options = current_options[current_options['ExpiryDate'] == expiry]
            days_to_expiry = expiry_options['days_to_expiry'].iloc[0]
            
            # Calculate reallocation rate based on days to expiry
            reallocation_rate = calculate_time_based_reallocation_rate(days_to_expiry)
            
            # Process CE options
            ce_options = expiry_options[expiry_options['StrikeType'] == 'CE']
            itm_ce = ce_options[ce_options['Strike'] <= current_spot]
            otm_ce = ce_options[ce_options['Strike'] > current_spot]
            
            # Process PE options
            pe_options = expiry_options[expiry_options['StrikeType'] == 'PE']
            itm_pe = pe_options[pe_options['Strike'] >= current_spot]
            otm_pe = pe_options[pe_options['Strike'] < current_spot]
            
            # Reallocate OI from ITM options to OTM options
            # CE reallocation
            if not itm_ce.empty and not otm_ce.empty:
                total_itm_ce_oi = itm_ce['OI'].sum()
                oi_to_move = int(total_itm_ce_oi * reallocation_rate)
                
                if oi_to_move > 0:
                    # Calculate weights for OTM strikes (higher weight for strikes closer to ATM)
                    weights = 1 / (1 + 0.01 * (otm_ce['Strike'] - current_spot))
                    weights = weights / weights.sum()
                    
                    # Distribute OI to OTM strikes
                    oi_distribution = (oi_to_move * weights).astype(int)
                    
                    # Reduce OI from ITM strikes proportionally
                    itm_reduction_factor = 1 - (oi_to_move / total_itm_ce_oi)
                    for idx in itm_ce.index:
                        current_options.loc[idx, 'OI'] = max(25, int(current_options.loc[idx, 'OI'] * itm_reduction_factor))
                    
                    # Add OI to OTM strikes
                    for idx, oi_add in zip(otm_ce.index, oi_distribution):
                        current_options.loc[idx, 'OI'] += oi_add
            
            # PE reallocation (similar logic)
            if not itm_pe.empty and not otm_pe.empty:
                total_itm_pe_oi = itm_pe['OI'].sum()
                oi_to_move = int(total_itm_pe_oi * reallocation_rate)
                
                if oi_to_move > 0:
                    # Calculate weights for OTM strikes (higher weight for strikes closer to ATM)
                    weights = 1 / (1 + 0.01 * (current_spot - otm_pe['Strike']))
                    weights = weights / weights.sum()
                    
                    # Distribute OI to OTM strikes
                    oi_distribution = (oi_to_move * weights).astype(int)
                    
                    # Reduce OI from ITM strikes proportionally
                    itm_reduction_factor = 1 - (oi_to_move / total_itm_pe_oi)
                    for idx in itm_pe.index:
                        current_options.loc[idx, 'OI'] = max(25, int(current_options.loc[idx, 'OI'] * itm_reduction_factor))
                    
                    # Add OI to OTM strikes
                    for idx, oi_add in zip(otm_pe.index, oi_distribution):
                        current_options.loc[idx, 'OI'] += oi_add
        
        # Update the main options dataframe
        options.loc[current_options.index, 'OI'] = current_options['OI']
    
    print("Sequential time processing completed.")
    return options
