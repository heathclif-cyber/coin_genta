"""
binance_client.py
Shared Binance API client with proxy support and fallback URLs.
Used by screener.py and node1_wyckoff.py.
"""
import os
import ccxt

# List of Binance API base URLs to try in order
BINANCE_API_URLS = [
    'https://api.binance.com',
    'https://api1.binance.com',
    'https://api2.binance.com',
    'https://api3.binance.com',
]

# Module-level singleton
_exchange = None

def create_exchange(proxy=None):
    """
    Create a ccxt Binance Spot exchange instance.
    Tries each API URL in BINANCE_API_URLS until one responds successfully.
    
    Args:
        proxy: Optional proxy URL (e.g., 'http://127.0.0.1:7890').
               If None, reads from HTTPS_PROXY environment variable.
    
    Returns:
        A configured ccxt.binance exchange instance, or None if all URLs fail.
    """
    # Check for proxy from argument or environment variable
    proxy_url = proxy or os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    
    for url in BINANCE_API_URLS:
        try:
            config = {
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                },
                'urls': {
                    'api': {
                        'public': url + '/api/v3',
                        'private': url + '/api/v3',
                        'sapi': url + '/sapi/v1',
                        'sapiV2': url + '/sapi/v2',
                        'sapiV3': url + '/sapi/v3',
                        'sapiV4': url + '/sapi/v4',
                    }
                },
                'timeout': 15000,
            }
            
            # Add proxy if available
            if proxy_url:
                config['proxies'] = {
                    'http': proxy_url,
                    'https': proxy_url,
                }
                print(f"  Using proxy: {proxy_url}")
            
            exchange = ccxt.binance(config)
            
            # Test connection with a lightweight call
            print(f"  Trying Binance API: {url} ...")
            exchange.fetch_ticker('BTC/USDT')
            
            print(f"  ✓ Connected successfully via {url}")
            return exchange
            
        except Exception as e:
            print(f"  ✗ Failed on {url}: {type(e).__name__}")
            continue
    
    print("  ✗ All Binance API URLs failed.")
    return None

def get_exchange(proxy=None):
    """
    Singleton: returns the cached exchange instance, or creates one.
    
    Args:
        proxy: Optional proxy URL.
    
    Returns:
        A configured ccxt.binance exchange instance.
    """
    global _exchange
    if _exchange is not None:
        return _exchange
    
    print("Initializing Binance Spot API with fallback URLs...")
    _exchange = create_exchange(proxy)
    
    if _exchange is None:
        print("ERROR: Could not connect to any Binance API endpoint.")
    
    return _exchange

# Self-test when run directly
if __name__ == "__main__":
    print("=== Binance Client Connection Test ===\n")
    ex = get_exchange()
    if ex:
        ticker = ex.fetch_ticker('BTC/USDT')
        print(f"\nBTC/USDT price: ${ticker['last']}")
    else:
        print("\nConnection failed on all endpoints.")
