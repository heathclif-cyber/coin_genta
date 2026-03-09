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
        
        # Drop rows with NaN values (e.g., the first 14 rows due to ATR calculation)
        df.dropna(inplace=True)
        df.reset_index(drop=True, inplace=True)
        
        return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def analyze_wyckoff_phase(df):
    """
    Analyzes the DataFrame to find Wyckoff Phase A characteristics,
    specifically the Selling Climax (SC).
    """
    if df is None or df.empty:
        print("Data is empty. Cannot analyze Wyckoff phases.")
        return None

    print("\nAnalyzing Wyckoff Phase A - Selling Climax (SC)...")
    
    # Target the first half of the data (e.g., first 90 days out of 180 original days)
    # Note: df already has some rows dropped due to ATR calculation (NaNs), 
    # so we take roughly the first half of the remaining data
    half_length = len(df) // 2
    first_half_df = df.iloc[:half_length].copy()
    
    # Find down days (Close < Open)
    down_days = first_half_df[first_half_df['close'] < first_half_df['open']]
    
    if down_days.empty:
        print("No down days found in the first half of the data.")
        return None
        
    # Find the day with the maximum volume among the down days
    sc_day = down_days.loc[down_days['volume'].idxmax()]
    
    # Extract values
    v_sc = sc_day['volume']
    atr_sc = sc_day['ATRr_14']
    sc_date = sc_day['timestamp']
    sc_close = sc_day['close']
    
    print(f"Selling Climax (SC) identified on: {sc_date.strftime('%Y-%m-%d')}")
    print(f" - SC Close Price: {sc_close}")
    print(f" - SC Volume (V_sc): {v_sc}")
    print(f" - SC ATR (ATR_sc): {atr_sc}")
    
    # Calculate 5-day averages for the most recent data (last 5 rows of the entire df)
    last_5_days = df.tail(5)
    v_test = last_5_days['volume'].mean()
    atr_test = last_5_days['ATRr_14'].mean()
    
    print(f"\nRecent 5-Day Averages (Test):")
    print(f" - Volume Test (V_test): {v_test}")
    print(f" - ATR Test (ATR_test): {atr_test}")
    
    # Mathematical Kill Switch logic: Calculate drops
    # Formula: Drop = (SC - Test) / SC * 100
    volume_drop = ((v_sc - v_test) / v_sc) * 100
    atr_drop = ((atr_sc - atr_test) / atr_sc) * 100
    
    print(f"\nAnalyzing Compression (Kill Switches):")
    print(f" - Volume Drop: {volume_drop:.2f}%")
    print(f" - ATR Drop: {atr_drop:.2f}%")
    
    # Both drops must be between 40% and 60%
    volume_valid = 40 <= volume_drop <= 60
    atr_valid = 40 <= atr_drop <= 60
    
    is_valid_wyckoff = volume_valid and atr_valid
    
    if is_valid_wyckoff:
        print(" => SUCCESS: Both Volume and ATR compression are within 40%-60% target.")
    else:
        print(" => FAILED: Compression targets not met.")
    
    return {
        'is_valid': is_valid_wyckoff,
        'sc_date': sc_date,
        'sc_close': sc_close,
        'v_sc': v_sc,
        'atr_sc': atr_sc,
        'v_test': v_test,
        'atr_test': atr_test,
        'volume_drop_pct': volume_drop,
        'atr_drop_pct': atr_drop,
        'sc_row_data': sc_day
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
        
        # Step 3: Only collect coins that passed both Kill Switch filters
        if result['is_valid']:
            passed_coins.append({
                'Symbol': symbol,
                'SC Date': result['sc_date'].strftime('%Y-%m-%d'),
                'SC Close': result['sc_close'],
                'Volume Drop (%)': round(result['volume_drop_pct'], 2),
                'ATR Drop (%)': round(result['atr_drop_pct'], 2),
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
