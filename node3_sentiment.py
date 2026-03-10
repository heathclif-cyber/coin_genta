import requests
import pandas as pd

# =========================================================
# Node 3: Sentiment & Divergence Audit
# Global market health check using Fear & Greed Index
# =========================================================

def get_fear_greed_index():
    """
    Fetches the latest Crypto Fear & Greed Index from alternative.me.
    Returns the integer score (0-100) and the classification string.
    """
    url = "https://api.alternative.me/fng/?limit=1"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data['data']:
            latest_data = data['data'][0]
            score = int(latest_data['value'])
            # We override their class with our internal status logic later, but we capture score
            return score
        else:
            return None
    except Exception as e:
        print(f"Error fetching Fear & Greed Index: {e}")
        return None

def main_node3(passed_onchain_coins):
    """
    Receives list of dictionaries from Node 2 (On-Chain phase).
    passed_onchain_coins structure: [{'Symbol': 'BTC/USDT', ...}, { ... }]
    """
    print("\n" + "=" * 60)
    print("  NODE 3 ANALYSIS: SENTIMENT & DIVERGENCE AUDIT")
    print("=" * 60)
    
    sentiment_passed_coins = []
    
    if not passed_onchain_coins:
        print("No coins received from Node 2.")
        return sentiment_passed_coins
        
    # 1. Fetch Global Market Sentiment once
    print("[*] Fetching Global Market Sentiment (Fear & Greed Index)...")
    score = get_fear_greed_index()
    
    if score is None:
        print("Failed to retrieve Global Sentiment. Aborting Node 3.")
        return sentiment_passed_coins
        
    print(f"    - Current Global Market Score: {score}")
    
    # 2. Institutional Validation Logic
    # We want Extreme Fear (0-24) to enter swings
    is_extreme_fear = score <= 24
    
    if is_extreme_fear:
        sentiment_status = '🟢 Valid (Extreme Fear)'
        overall_validation = '🟢 Passed'
        print("    => MARKET STATUS: EXTREME FEAR (IDEAL FOR ENTRY). ALL COINS PASSED.")
    else:
        sentiment_status = '🔴 Invalid (Neutral/Greed)'
        overall_validation = '🔴 Failed'
        print("    => MARKET STATUS: NOT IN EXTREME FEAR YET. COINS REJECTED.")
        print(f"    - Wait for score <= 24 to trigger entry.")
        
    # 3. Append Global Sentiment to individual coin payloads
    for coin in passed_onchain_coins:
        coin_record = coin.copy() # Avoid mutating original reference
        
        coin_record['Sentiment Score'] = score
        coin_record['Sentiment Status'] = sentiment_status
        coin_record['Node 3 Validation'] = overall_validation
        
        # Only add to final output array if the global market passed
        if is_extreme_fear:
            sentiment_passed_coins.append(coin_record)
            
    print("\n" + "=" * 60)
    print("  FINAL NODE 3 RESULT (MARKET TIMING ENABLED)")
    print("=" * 60)
    
    if sentiment_passed_coins:
        result_df = pd.DataFrame(sentiment_passed_coins)
        print(result_df.to_string(index=False))
        return result_df
    else:
        print("No coins passed Node 3 (Market Conditions Unfavorable).")
        # Return empty dataframe
        return pd.DataFrame()
