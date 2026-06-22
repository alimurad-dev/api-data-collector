import os
import json
import ssl
from datetime import datetime
import urllib3
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Local setup ke liye environment files load karega
load_dotenv()
DB_URI = os.getenv("NEON_DATABASE_URL")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_and_save_to_cloud():
    print("Connecting to Yahoo Finance API...")
    
    # Financial Endpoint Configuration
    url = "https://yahoo.com"
    tickers_string = "BTC-USD,ETH-USD,BNB-USD,SOL-USD,ADA-USD"
    
    # Cloud-grade SSL Handshake Initialization
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    http = urllib3.PoolManager(ssl_context=ctx, timeout=12.0)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        # Fetching true dynamic global market response
        response = http.request('GET', url, fields={"symbols": tickers_string}, headers=headers)
        raw_data = response.data.decode('utf-8').strip()
        
        parsed_payload = json.loads(raw_data)
        result_list = parsed_payload.get("quoteResponse", {}).get("result", [])
        
        if not result_list:
            raise ValueError("Empty transmission received from data endpoint.")
            
        print("SUCCESS: Live financial stream successfully parsed.")
        
    except Exception as network_err:
        print(f"Network Failure: Could not catch live values ({network_err})")
        print("Terminating transaction to prevent fake database injection.")
        return

    try:
        if not DB_URI:
            raise ValueError("Configuration Error: Connection string missing from cloud registry.")
            
        # Create persistent connection pool
        engine = create_engine(DB_URI, pool_pre_ping=True)
        current_time = datetime.now()
        
        name_map = {
            "BTC-USD": ("Bitcoin", "BTC"), "ETH-USD": ("Ethereum", "ETH"),
            "BNB-USD": ("Binance Coin", "BNB"), "SOL-USD": ("Solana", "SOL"),
            "ADA-USD": ("Cardano", "ADA")
        }

        with engine.begin() as connection:
            # Ensure the cloud database table architecture matches perfectly
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS crypto_prices (
                    id SERIAL PRIMARY KEY,
                    coin_name VARCHAR(100),
                    symbol VARCHAR(10),
                    current_price NUMERIC,
                    market_cap BIGINT,
                    fetched_at TIMESTAMP
                )
            """))

            count = 0
            for crypto in result_list:
                symbol_raw = crypto.get('symbol')
                if symbol_raw in name_map:
                    name, clean_symbol = name_map[symbol_raw]
                    
                    # Fetching original transaction prices from live web payload
                    actual_price = float(crypto.get('regularMarketPrice', 0))
                    actual_market_cap = int(crypto.get('marketCap', 0))

                    insert_query = text("""
                        INSERT INTO crypto_prices (coin_name, symbol, current_price, market_cap, fetched_at)
                        VALUES (:name, :symbol, :price, :market_cap, :fetched_at)
                    """)
                    
                    connection.execute(insert_query, {
                        "name": name, "symbol": clean_symbol, "price": actual_price,
                        "market_cap": actual_market_cap, "fetched_at": current_time
                    })
                    count += 1
            
            print(f"PIPELINE SUCCESS: {count} actual real market rows pushed to Neon Cloud.")

    except Exception as db_err:
        print(f"Database Pool Exception: Execution aborted ({db_err})")

if __name__ == "__main__":
    fetch_and_save_to_cloud()
