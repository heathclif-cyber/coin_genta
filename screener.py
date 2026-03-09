import pandas as pd
import ccxt
import requests
import time

# Menginisialisasi koneksi ke bursa Binance secara khusus untuk pasar Spot
exchange = ccxt.binance({
    # Sangat penting untuk menghindari blokir IP: mengaktifkan rate limiter bawaan CCXT
    'enableRateLimit': True, 
    
    # Memaksa CCXT untuk menggunakan API endpoint untuk pasar Spot (bukan Futures/Margin)
    'options': {
        'defaultType': 'spot',
    }
})

# Suppress initial print statements to keep API responses clean
# print("Pustaka berhasil diimpor.")
# print(f"Bursa yang diinisialisasi: {exchange.name} ({exchange.options['defaultType']})")

def get_top_100_coins():
    """
    Mengambil data 100 koin teratas berdasarkan kapitalisasi pasar dari API CoinGecko.
    Akan mengabaikan stablecoin tertentu.
    """
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': 100,
        'page': 1,
        'sparkline': False
    }
    
    # Daftar stablecoin yang harus diabaikan
    stablecoins = ['USDT', 'USDC', 'DAI', 'FDUSD', 'TUSD', 'USDD']
    symbols = []
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Memastikan respons API 200 OK
        data = response.json()
        
        for coin in data:
            symbol = coin['symbol'].upper()
            if symbol not in stablecoins:
                symbols.append(symbol)
                
        print(f"Berhasil mengunduh daftar {len(symbols)} koin (Non-Stablecoin) dari Top 100.")
        return symbols
    except Exception as e:
        print(f"Error saat mengambil data dari CoinGecko: {e}")
        return []

def get_price_data(symbols):
    """
    Mengambil data OHLCV harian (1D) selama 60 hari terakhir.
    Menyimpan data penutupan terakhir dan harga tertinggi (local high).
    """
    results = []
    
    # Memastikan BTC ada di awal list untuk baseline
    if 'BTC' in symbols:
        symbols.remove('BTC')
    symbols = ['BTC'] + symbols

    print(f"Mulai mengambil data untuk {len(symbols)} koin...")

    for symbol in symbols:
        # Menambahkan format /USDT
        ticker = f"{symbol}/USDT"
        
        try:
            # fetch_ohlcv(symbol, timeframe, since, limit)
            # limit=60 akan mengambil 60 candle terakhir
            ohlcv = exchange.fetch_ohlcv(ticker, timeframe='1d', limit=60)
            
            if ohlcv and len(ohlcv) > 0:
                # Kolom response dari fetch_ohlcv: [Timestamp, Open, High, Low, Close, Volume]
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                
                # Harga penutupan terakhir (baris paling akhir, kolom close)
                last_close = df['close'].iloc[-1]
                
                # Harga tertinggi dari 60 hari tersebut
                local_high = df['high'].max()
                
                # Menghitung persentase koreksi penurunan maksimum (Drawdown)
                if local_high > 0:
                    drawdown = ((local_high - last_close) / local_high) * 100
                else:
                    drawdown = 0.0
                
                results.append({
                    'Symbol': symbol,
                    'Ticker': ticker,
                    'Last Close': last_close,
                    '60D High': local_high,
                    'Drawdown (%)': drawdown
                })
            else:
                print(f"Data kosong untuk {ticker}")
                
        except Exception as e:
            print(f"Error mengambil data {ticker}: {e}")
            
        # Jeda 0.1 detik untuk menghindari Rate Limit Binance
        time.sleep(0.1)
        
    # Mengembalikan dalam bentuk Pandas DataFrame
    df_results = pd.DataFrame(results)
    
    # Menambahkan kalkulasi Relative_Strength_R
    if not df_results.empty and 'Drawdown (%)' in df_results.columns:
        # Mengambil nilai drawdown BTC
        btc_data = df_results[df_results['Symbol'] == 'BTC']
        
        if not btc_data.empty:
            btc_drawdown = btc_data['Drawdown (%)'].values[0]
            
            # Error handling: jika drawdown BTC = 0, R tidak bisa dihitung (dibagi dengan nol)
            if btc_drawdown != 0:
                df_results['Relative_Strength_R'] = df_results['Drawdown (%)'] / btc_drawdown
            else:
                print("Peringatan: Drawdown BTC bernilai 0. Relative_Strength_R di-set None (menghindari pembagian dengan nol).")
                df_results['Relative_Strength_R'] = None
        else:
            print("Peringatan: Data BTC tidak lengkap/tidak ditemukan. Relative_Strength_R tidak dapat dihitung.")
            df_results['Relative_Strength_R'] = None
    else:
        # Jika hasil kosong
        df_results['Relative_Strength_R'] = None
            
    # ------ FILTER GENUINE ALPHA ------
    # Memastikan tidak mengalami error terkait tipe data atau None
    if 'Relative_Strength_R' in df_results.columns and not df_results.empty:
        # Mengubah nilai yg mungkin None/NaN menjadi format float yang bisa difilter
        df_results['Relative_Strength_R'] = pd.to_numeric(df_results['Relative_Strength_R'], errors='coerce')
        
        # HANYA menampilkan koin dengan R < 2.0 (Drop NaN/None yang tidak valid)
        df_filtered = df_results[df_results['Relative_Strength_R'] < 2.0].copy()
        
        # Urutkan dari R terkecil hingga terbesar
        df_filtered = df_filtered.sort_values(by='Relative_Strength_R', ascending=True)
        
        # Kembalikan dataframe yang sudah difilter
        return df_filtered
def run_scanner():
    """Wrapper function to be called by the Flask API."""
    list_koin = get_top_100_coins()
    if list_koin:
        df_harga = get_price_data(list_koin)
        if df_harga is not None and not df_harga.empty:
            # Convert NaN to None for JSON serialization
            df_harga = df_harga.where(pd.notnull(df_harga), None)
            return df_harga.to_dict(orient='records')
    return []

# ==========================================
# BLOK EKSEKUSI UTAMA (Untuk testing CLI)
# ==========================================
if __name__ == "__main__":
    print("\n--- SKRIP SCREENER DIMULAI ---")
    
    # 1. Mendapatkan daftar Top Koin
    list_koin = get_top_100_coins()
    
    # 2. Jika sukses, ambil data harganya dan filter!
    if list_koin:
        print("\nMemulai pengunduhan data OHLCV...")
        df_harga = get_price_data(list_koin)
        
        print("\n--- ACTIVE WATCHLIST (GENUINE ALPHA) ---")
        if df_harga is not None and not df_harga.empty:
            print(df_harga.to_string(index=False))
        else:
            print("Tidak ada koin yang lolos filter kelayakan (R < 2.0).")
            
    print("\n--- SELESAI ---")
