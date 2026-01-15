import pandas as pd
import numpy as np
import random

def generate_mock_data(days=100):
    """Generates mock OHLCV and Turnover date."""
    dates = pd.date_range(start="2023-01-01", periods=days, freq="D")
    data = []
    
    price = 10.0
    for date in dates:
        # Random walk for price
        change = random.uniform(-0.05, 0.05)
        price = price * (1 + change)
        
        high = price * (1 + random.uniform(0, 0.02))
        low = price * (1 - random.uniform(0, 0.02))
        open_p = random.uniform(low, high)
        close_p = random.uniform(low, high)
        
        # Turnover rate (換手率) between 0.5% and 5%
        turnover = random.uniform(0.005, 0.05)
        
        data.append({
            "date": date,
            "open": open_p,
            "high": high,
            "low": low,
            "close": close_p,
            "turnover": turnover
        })
        
    return pd.DataFrame(data)

def calculate_chip_distribution(df, price_precision=0.1):
    """
    Calculates Chip Distribution (CYQ).
    
    Logic:
    Total Chips = 100% (represented as 1.0)
    Each day:
    1. Existing chips decay by (1 - turnover_rate).
    2. New chips (turnover_rate) are added at the current day's price.
       For simplicity, new chips are distributed uniformly between Low and High.
    """
    
    # 1. Determine global price range to set up bins
    min_price = df['low'].min() * 0.9
    max_price = df['high'].max() * 1.1
    
    # Create price bins
    bins = np.arange(min_price, max_price, price_precision)
    # chips represents the volume of chips at each price bin index
    chips = np.zeros(len(bins))
    
    print(f"Calculating CYP for {len(df)} days...")
    print(f"Price range: {min_price:.2f} - {max_price:.2f} (bins: {len(bins)})")
    
    for i, row in df.iterrows():
        turnover = row['turnover']
        high = row['high']
        low = row['low']
        avg = (row['open'] + row['close'] + high + low) / 4 # approximated avg price
        
        # A. Decay existing chips
        # If turnover is 100% (1.0), all old chips are gone.
        # If turnover is 10% (0.1), 90% of old chips remain.
        chips = chips * (1 - turnover)
        
        # B. Add new chips
        # Identify which bins cover the day's [low, high] range
        # Start index in bins
        start_idx = int((low - min_price) / price_precision)
        end_idx = int((high - min_price) / price_precision)
        
        # Clamp indices
        start_idx = max(0, start_idx)
        end_idx = min(len(bins) - 1, end_idx)
        
        if end_idx >= start_idx:
            # Number of bins covered
            num_bins = end_idx - start_idx + 1
            
            # Simple Uniform Distribution: distribute 'turnover' amount equally
            # A better model uses Triangular distribution centered at avg price
            
            # Implementation of Triangular-like mass addition
            # We add 'turnover' mass total.
            
            # For simplicity in this prototype: Uniform
            chips_per_bin = turnover / num_bins
            chips[start_idx : end_idx + 1] += chips_per_bin
            
    # Normalize result (handling floating point drift, though logically it should stay near 1.0 if started at 0 and added gradually? 
    # Actually, if we start at 0, it takes time to build up to 1.
    # Usually, we assume an initial distribution or run for enough period so initial state matters less.
    # Let's verify sum.
    total_chips = np.sum(chips)
    
    return bins, chips, total_chips

# --- Run Demo ---
if __name__ == "__main__":
    # 1. Generate Data
    df = generate_mock_data(days=120)
    print("Generated Mock Data (Last 5 days):")
    print(df.tail())
    print("-" * 30)
    
    # 2. Calculate
    bins, chips, total_mass = calculate_chip_distribution(df)
    
    print(f"\nCalculation Complete.")
    print(f"Total Chip Mass: {total_mass:.4f} (Should approach 1.0)")
    
    # 3. Visualization output (Text based)
    print("\n--- Chip Distribution Peak Preview (Last Day) ---")
    
    # Combine bins and chips
    distribution = list(zip(bins, chips))
    # Sort by chip density (highest first) to find peaks
    sorted_dist = sorted(distribution, key=lambda x: x[1], reverse=True)
    
    print("Top 5 Price Levels with Heaviest Chips (Support/Resistance):")
    for price, density in sorted_dist[:5]:
        print(f"Price: {price:.2f} | Density: {density:.6f}")
        
    print("\nText-based Histogram (Sample):")
    # Show a slice of the distribution around the current price
    current_price = df.iloc[-1]['close']
    print(f"Current Price: {current_price:.2f}")
    
    idx = int((current_price - bins[0]) / (bins[1] - bins[0]))
    window = 10
    start = max(0, idx - window)
    end = min(len(bins), idx + window)
    
    for i in range(start, end):
        p = bins[i]
        c = chips[i]
        bar = '#' * int(c * 5000) # scale for display
        marker = "<-- Current" if i == idx else ""
        print(f"{p:.2f} : {bar} {c:.5f} {marker}")
