import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
DB_URI = os.getenv("NEON_DATABASE_URL")

def generate_crypto_report():
    try:
        if not DB_URI:
            raise ValueError("Configuration connection string missing.")
            
        engine = create_engine(DB_URI, pool_pre_ping=True)
        
        # Pulls the most recently pushed transactional rows from Neon Cloud
        query = text("""
            SELECT coin_name, symbol, current_price, market_cap, fetched_at 
            FROM crypto_prices 
            ORDER BY fetched_at DESC 
            LIMIT 5;
        """)

        with engine.connect() as connection:
            result = connection.execute(query)
            rows = result.fetchall()

        if not rows:
            print("Alert: Cloud table repository contains no rows.")
            return

        print("\n" + "=" * 85)
        print(f"LIVE REAL-TIME FINANCIAL REPORT | Checked At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 85)
        print(f"{'Coin Name':<18} | {'Symbol':<8} | {'Price (USD)':<12} | {'Market Cap (USD)':<18} | {'Fetched At':<20}")
        print("-" * 85)

        for row in rows:
            name, symbol, price, market_cap, fetched_at = row
            formatted_time = fetched_at.strftime("%Y-%m-%d %H:%M")

            # Native formatting conversions to string values
            price_str = f"${float(price):,.2f}"
            cap_str = f"${int(market_cap):,}"

            print(f"{name:<18} | {symbol:<8} | {price_str:<12} | {cap_str:<18} | {formatted_time:<20}")

        print("=" * 85)
        print("SUCCESS: Display terminal populated with live production data rows.\n")

    except Exception as db_err:
        print(f"Display Pipeline Failure: Connection error ({db_err})")

if __name__ == "__main__":
    generate_crypto_report()
