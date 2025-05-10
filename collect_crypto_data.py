import requests
import pandas as pd
import schedule
import time
from datetime import datetime
import os

last_date_seen = None
last_major_cycle = None

def fetch_combined_bitcoin_data():
    global last_date_seen, last_major_cycle
    now = datetime.now()

    # ✅ Step 1: Get historical price data (no interval param)
    price_url = 'https://api.coingecko.com/api/v3/coins/bitcoin/market_chart'
    price_params = {
        'vs_currency': 'usd',
        'days': '2'  # Don't specify interval — CoinGecko will auto-select hourly
    }

    try:
        price_response = requests.get(price_url, params=price_params)
        price_data = price_response.json()

        if 'prices' not in price_data:
            print(f"[{now.strftime('%H:%M:%S')}] No 'prices' in response. Full response:")
            print(price_data)
            return

        df_price = pd.DataFrame(price_data['prices'], columns=['Timestamp', 'Price'])
        df_price['Date'] = pd.to_datetime(df_price['Timestamp'], unit='ms')
        df_price = df_price[['Date', 'Price']]
        latest_data_time = df_price['Date'].max()

        if last_date_seen is not None and latest_data_time <= last_date_seen:
            print(f"[{now.strftime('%H:%M:%S')}] No new data to append.")
            return

        last_date_seen = latest_data_time

        # ✅ Step 2: Get market features (live snapshot)
        market_url = 'https://api.coingecko.com/api/v3/coins/markets'
        market_params = {
            'vs_currency': 'usd',
            'ids': 'bitcoin',
            'sparkline': False
        }

        market_response = requests.get(market_url, params=market_params)
        market_data = market_response.json()[0]

        features = {
            'current_price': market_data['current_price'],
            'market_cap': market_data['market_cap'],
            'market_cap_rank': market_data['market_cap_rank'],
            'total_volume': market_data['total_volume'],
            'circulating_supply': market_data['circulating_supply'],
            'max_supply': market_data['max_supply'],
            'ath': market_data['ath'],
            'atl': market_data['atl'],
            'price_change_1h': market_data.get('price_change_percentage_1h_in_currency'),
            'price_change_24h': market_data['price_change_percentage_24h'],
            'price_change_7d': market_data.get('price_change_percentage_7d_in_currency'),
            'price_change_30d': market_data.get('price_change_percentage_30d_in_currency'),
            'price_change_1y': market_data.get('price_change_percentage_1y_in_currency'),
            'last_updated': market_data['last_updated']
        }

        latest_row = df_price[df_price['Date'] == latest_data_time].copy()
        for key, value in features.items():
            latest_row[key] = value

        file_name = 'bitcoin_full_data.csv'
        if os.path.exists(file_name):
            existing = pd.read_csv(file_name)
            existing['Date'] = pd.to_datetime(existing['Date'])
            df_final = pd.concat([existing, latest_row])
            df_final = df_final.drop_duplicates(subset='Date')
            df_final = df_final.sort_values(by='Date')
        else:
            df_final = latest_row
            print(f"[{now.strftime('%H:%M:%S')}] Creating new data file.")

        df_final.to_csv(file_name, index=False)
        print(f"[{now.strftime('%H:%M:%S')}] Combined data saved. Rows: {len(df_final)}")

        if last_major_cycle is None or (now - last_major_cycle).seconds >= 1800:
            print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Major update cycle.")
            last_major_cycle = now

    except Exception as e:
        print(f"[{now.strftime('%H:%M:%S')}] Error: {e}")

# Schedule the function to run every 3 minutes
schedule.every(3).minutes.do(fetch_combined_bitcoin_data)

# Run once at the start
fetch_combined_bitcoin_data()

print("Scheduler started. Collecting Bitcoin full data every 3 minutes.\n")

while True:
    schedule.run_pending()
    time.sleep(1)
