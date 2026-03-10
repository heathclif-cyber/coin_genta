import pandas as pd
import time
import random

# =========================================================
# Node 2: On-Chain Data Analysis (Mock Integration)
# Simulated API to replicate Glassnode/CryptoQuant logic
# =========================================================

def mock_onchain_api_call(symbol, metric):
    """
    Simulates fetching on-chain data for a specific metric.
    In production, replace this with requests.get() to an actual API provider.
    """
    # Simulate network latency
    time.sleep(0.1)
    
    # 1. Netflow Simulation
    # Generates a list of Netflow values over the last 3 days
    if metric == 'netflow':
        # 60% chance to be valid (negative sum over 3 days)
        if random.random() < 0.6:
            return [random.uniform(-1000, -100) for _ in range(3)] # Consistent Outflows
        else:
            return [random.uniform(-500, 1000) for _ in range(3)]  # Mixed or Inflows
            
    # 2. Wallet Age Simulation (Mature vs New Wallets)
    # Returns percentage (0-100) of volume coming from mature wallets (>48h)
    elif metric == 'wallet_age':
        # We want > 70% to pass
        # 50% chance to be valid
        return random.uniform(50.0, 95.0)
        
    # 3. Stablecoin Supply Ratio (SSR) Oscillator
    # Returns a simulated SSR quartile status
    elif metric == 'ssr_index':
        # 'Low' (Quartile 1) is valid, meaning high buying power
        # 40% chance to be valid
        return random.choice(['Low (Q1)', 'Mid-Low (Q2)', 'Mid-High (Q3)', 'High (Q4)'])

    return None

def check_netflow(symbol):
    """
    Valid if Total Netflow is Negative (Outflow > Inflow) for the last 3 days.
    """
    data_3d = mock_onchain_api_call(symbol, 'netflow')
    
    # Check if ALL 3 days are negative
    is_valid = all(day_flow < 0 for day_flow in data_3d)
    
    # Calculate sum for display
    total_netflow = sum(data_3d)
    
    status_text = '🟢 Valid' if is_valid else '🔴 Invalid'
    desc = f"{status_text} (Total: {total_netflow:,.0f} coins)"
    
    return is_valid, desc

def filter_wallet_age(symbol):
    """
    Valid if > 70% of transaction volume comes from >48hr old wallets.
    """
    mature_ratio = mock_onchain_api_call(symbol, 'wallet_age')
    
    is_valid = mature_ratio > 70.0
    
    status_text = '🟢 Valid' if is_valid else '🔴 Invalid'
    desc = f"{status_text} (Ratio: {mature_ratio:.1f}%)"
    
    return is_valid, desc

def check_ssr_index(symbol):
    """
    Valid if the SSR score is in the lower quartile ('Low (Q1)').
    """
    ssr_quartile = mock_onchain_api_call(symbol, 'ssr_index')
    
    is_valid = ssr_quartile == 'Low (Q1)'
    
    status_text = '🟢 Valid' if is_valid else '🔴 Invalid'
    desc = f"{status_text} ({ssr_quartile})"
    
    return is_valid, desc

def main_node2(passed_vcp_coins):
    """
    Receives list of dictionaries from Node 1 (VCP phase).
    passed_vcp_coins structure: [{'Symbol': 'BTC/USDT', ...}, { ... }]
    """
    print("\n" + "=" * 60)
    print("  NODE 2 ANALYSIS: ON-CHAIN VERIFICATION (SIMULATED API)")
    print("=" * 60)
    
    onchain_passed_coins = []
    
    if not passed_vcp_coins:
        print("No coins received from Node 1.")
        return onchain_passed_coins
        
    for coin in passed_vcp_coins:
        symbol = coin['Symbol']
        print(f"[*] Running On-Chain verification for {symbol}...")
        
        # 1. Netflow Filter
        netflow_pass, netflow_desc = check_netflow(symbol)
        
        # 2. Wallet Age Filter
        wallet_pass, wallet_desc = filter_wallet_age(symbol)
        
        # 3. SSR Filter
        ssr_pass, ssr_desc = check_ssr_index(symbol)
        
        # Overall Validation: Requires ALL 3 to pass
        overall_valid = netflow_pass and wallet_pass and ssr_pass
        
        print(f"    - Netflow: {netflow_desc}")
        print(f"    - Wallet Age: {wallet_desc}")
        print(f"    - SSR Index: {ssr_desc}")
        
        if overall_valid:
            print("    => SUCCESS: Node 2 Passed!")
            onchain_passed_coins.append({
                'Symbol': symbol,
                # Include previous node data if needed, or just on-chain data
                'VCP Start Date': coin.get('Start Date', '-'),
                'VCP End Date': coin.get('End Date', '-'),
                'Netflow Status': netflow_desc,
                'Wallet Age Ratio': wallet_desc,
                'SSR Status': ssr_desc,
                'Overall On-Chain Validation': '🟢 Passed'
            })
        else:
            print("    => FAILED: Did not meet all 3 on-chain criteria.")
            
    print("\n" + "=" * 60)
    print("  FINAL NODE 2 RESULT (CLEARED ALL VCP + ON-CHAIN)")
    print("=" * 60)
    
    if onchain_passed_coins:
        result_df = pd.DataFrame(onchain_passed_coins)
        print(result_df.to_string(index=False))
        return result_df
    else:
        print("No coins passed Node 2.")
        return pd.DataFrame() # Return empty DataFrame
