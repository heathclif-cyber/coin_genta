import pandas as pd
import pandas_ta as ta
import ccxt
import time

# Module-level variable for Binance API
binance = None

def init_binance():
    """Initialize Binance Spot API (called once)."""
    global binance
    if binance is not None:
        return binance
    try:
        binance = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        print("Binance Spot API initialized successfully.")
    except Exception as e:
        print(f"Error initializing API: {e}")
    return binance

def get_long_term_data(symbol):
    init_binance()
    try:
        print(f"Fetching 180 days of 1d data for {symbol}...")
        # Fetch daily data (1d) for the last 180 days
        ohlcv = binance.fetch_ohlcv(symbol, '1d', limit=180)
        
        # Convert to Pandas DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Calculate ATR (Average True Range) period 14
        df.ta.atr(length=14, append=True)
        
        # Calculate 20-day Simple Moving Average (SMA) of Volume
        df['SMA_20_Vol'] = df['volume'].rolling(window=20).mean()
        
        # Drop rows with NaN values (e.g., the first 14 rows due to ATR calculation)
        df.dropna(inplace=True)
        df.reset_index(drop=True, inplace=True)
        
        return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def analyze_wyckoff_phase(df):
    """
    Analyzes the DataFrame for Volatility Contraction Pattern (VCP) characteristics.
    Requires 3 conditions to pass:
    1. Volume Dry-Up
    2. ATR Contraction
    3. Tight Range Action
    """
    if df is None or df.empty or len(df) < 60:
        print("Data is empty or insufficient (< 60 days). Cannot analyze VCP.")
        return None

    print("\nAnalyzing Volatility Contraction Pattern (VCP)...")
    
    # --- 1. Volume Dry-Up ---
    # Average volume of the last 3 days
    last_3_days = df.tail(3)
    vol_current = last_3_days['volume'].mean()
    
    # SMA_20_Vol on the most recent day
    vol_ma20 = df.iloc[-1]['SMA_20_Vol']
    
    # Calculate Dry-Up Percentage
    vol_dry_up_pct = 0
    if vol_ma20 > 0:
        vol_dry_up_pct = (1 - (vol_current / vol_ma20)) * 100
        
    # Condition: vol_current <= vol_ma20 * 0.7  => (dry up >= 30%)
    vol_valid = vol_current <= (vol_ma20 * 0.70)
    
    print(f" - Vol Current (3d avg): {vol_current:.2f}")
    print(f" - Vol MA20: {vol_ma20:.2f}")
    print(f"   => Volume Dry-Up: {vol_dry_up_pct:.2f}% (Valid: {vol_valid})")

    # --- 2. ATR Contraction ---
    # Average ATR of the last 3 days
    atr_current = last_3_days['ATRr_14'].mean()
    
    # Peak ATR over the last 60 days
    last_60_days = df.tail(60)
    atr_peak = last_60_days['ATRr_14'].max()
    
    # Calculate ATR Shrinkage Percentage
    atr_shrinkage_pct = 0
    if atr_peak > 0:
        atr_shrinkage_pct = (1 - (atr_current / atr_peak)) * 100
        
    # Condition: atr_current <= atr_peak * 0.50 => (shrinkage >= 50%)
    atr_valid = atr_current <= (atr_peak * 0.50)
    
    print(f" - ATR Current (3d avg): {atr_current:.4f}")
    print(f" - Peak ATR (60d): {atr_peak:.4f}")
    print(f"   => ATR Shrinkage: {atr_shrinkage_pct:.2f}% (Valid: {atr_valid})")

    # --- 3. Tight Range Action ---
    # Max High, Min Low, and Avg Close over the last 21 days
    last_21_days = df.tail(21)
    max_high = last_21_days['high'].max()
    min_low = last_21_days['low'].min()
    avg_price = last_21_days['close'].mean()
    
    price_range = max_high - min_low
    
    # Calculate Price Range Percentage relative to avg price
    price_range_pct = 0
    if avg_price > 0:
        price_range_pct = (price_range / avg_price) * 100
        
    # Condition: price_range < avg_price * 0.10 => (range < 10%)
    range_valid = price_range_pct < 10.0
    
    print(f" - 21d Max High: {max_high:.4f}, Min Low: {min_low:.4f}")
    print(f" - 21d Avg Price: {avg_price:.4f}")
    print(f"   => Price Range: {price_range_pct:.2f}% (Valid: {range_valid})")
    
    # --- Final Validation ---
    is_valid_vcp = vol_valid and atr_valid and range_valid
    
    if is_valid_vcp:
        print(" => SUCCESS: All 3 VCP conditions met!")
    else:
        print(" => FAILED: VCP conditions not met.")
    
    return {
        'is_valid': is_valid_vcp,
        'vol_dry_up_pct': vol_dry_up_pct,
        'atr_shrinkage_pct': atr_shrinkage_pct,
        'price_range_pct': price_range_pct,
        'sc_date': df.iloc[-1]['timestamp'] # Provide latest date for UI compatibility
    }

def main_node1(watchlist_symbols):
    """
    Main function for Node 1: Wyckoff Price Structure.
    Receives a list of coin symbols (e.g., ['PENDLE/USDT', 'XRP/USDT']),
    analyzes each one, and returns a DataFrame of coins that passed validation.
    """
    init_binance()
    print("=" * 60)
    print("  NODE 1: WYCKOFF PRICE STRUCTURE FILTER")
    print("=" * 60)
    print(f"Processing {len(watchlist_symbols)} coins...\n")
    
    passed_coins = []
    
    for symbol in watchlist_symbols:
        print(f"\n{'─' * 40}")
        print(f"  Analyzing: {symbol}")
        print(f"{'─' * 40}")
        
        # Step 1: Fetch long-term data
        df = get_long_term_data(symbol)
        if df is None:
            print(f"  [SKIP] Could not fetch data for {symbol}")
            continue
        
        # Step 2: Analyze Wyckoff Phase and apply Kill Switches
        result = analyze_wyckoff_phase(df)
        if result is None:
            print(f"  [SKIP] Could not analyze {symbol}")
            continue
        
        # Step 3: Only collect coins that passed all VCP filters
        if result['is_valid']:
            passed_coins.append({
                'Symbol': symbol,
                'Date': result['sc_date'].strftime('%Y-%m-%d'),
                'Volume Dry-Up (%)': round(result['vol_dry_up_pct'], 2),
                'ATR Shrinkage (%)': round(result['atr_shrinkage_pct'], 2),
                'Price Range (%)': round(result['price_range_pct'], 2),
            })
        
        # Respect API rate limits
        time.sleep(0.5)
    
    # Build final DataFrame of passed coins only
    print("\n" + "=" * 60)
    print("  NODE 1 RESULT: COINS THAT PASSED WYCKOFF VALIDATION")
    print("=" * 60)
    
    if passed_coins:
        result_df = pd.DataFrame(passed_coins)
        print(result_df.to_string(index=False))
        return result_df
    else:
        print("No coins passed the Wyckoff Phase A validation.")
        return pd.DataFrame()

if __name__ == "__main__":
    init_binance()
    # Example watchlist from Screener
    watchlist = ['PENDLE/USDT', 'XRP/USDT', 'BTC/USDT', 'ETH/USDT', 'SOL/USDT']
    result_df = main_node1(watchlist)
