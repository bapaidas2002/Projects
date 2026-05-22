# ============================================================
# DOWNLOAD 1 YEAR NIFTY 50 5-MINUTE DATA USING UPSTOX API
# ============================================================
# This script:
# 1. Downloads NIFTY 50 5-minute candle data
# 2. Uses 3-month chunks to avoid API errors
# 3. Combines all chunks into one dataframe
# 4. Saves final dataset into CSV
# ============================================================
import websockets
import requests
import pandas as pd
import time

from datetime import datetime, timedelta

# ============================================================
# YOUR ACCESS TOKEN
# ============================================================

ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI3NkI0VEYiLCJqdGkiOiI2YTBlOWFkNWVlMjE3ZDc1NjJiMzZkM2QiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzc5MzQyMDM3LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3Nzk0MDA4MDB9.1u3rRD9OUMlTag58WituWc-xMky76PE8XI4y0oVBVis"

# ============================================================
# NIFTY 50 INSTRUMENT KEY
# ============================================================

INSTRUMENT_KEY = "NSE_INDEX|Nifty 50"

# ============================================================
# API DETAILS
# ============================================================

headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

# ============================================================
# UPSTOX HISTORICAL API URL
# ============================================================

BASE_URL = "https://api.upstox.com/v2/historical-candle"

# ============================================================
# DATE RANGE
# ============================================================

end_date = datetime.now()

start_date = end_date - timedelta(days=365)

# ============================================================
# SPLIT INTO 3-MONTH CHUNKS
# ============================================================

chunk_size_days = 90

all_dataframes = []

current_start = start_date

# ============================================================
# LOOP THROUGH CHUNKS
# ============================================================

while current_start < end_date:

    current_end = min(
        current_start + timedelta(days=chunk_size_days),
        end_date
    )

    from_date = current_start.strftime("%Y-%m-%d")
    to_date = current_end.strftime("%Y-%m-%d")

    print("\n======================================")
    print(f"Fetching: {from_date} -> {to_date}")
    print("======================================")

    # ========================================================
    # API URL
    # ========================================================

    url = (
        f"{BASE_URL}/"
        f"{INSTRUMENT_KEY}/"
        f"5minute/"
        f"{to_date}/"
        f"{from_date}"
    )

    try:

        response = requests.get(
            url,
            headers=headers
        )

        data = response.json()

        print("\nAPI STATUS:")
        print(response.status_code)

        # ====================================================
        # CHECK API RESPONSE
        # ====================================================

        if 'data' not in data:

            print("\nNo data found.")
            print(data)

            current_start = current_end

            continue

        candles = data['data']['candles']

        # ====================================================
        # CREATE DATAFRAME
        # ====================================================

        df = pd.DataFrame(
            candles,
            columns=[
                'Datetime',
                'Open',
                'High',
                'Low',
                'Close',
                'Volume',
                'OpenInterest'
            ]
        )

        # ====================================================
        # CONVERT DATETIME
        # ====================================================

        df['Datetime'] = pd.to_datetime(df['Datetime'])

        # ====================================================
        # SORT DATA
        # ====================================================

        df.sort_values(
            by='Datetime',
            inplace=True
        )

        print("\nRows fetched:", len(df))

        # ====================================================
        # STORE CHUNK
        # ====================================================

        all_dataframes.append(df)

        # ====================================================
        # WAIT TO AVOID RATE LIMIT
        # ====================================================

        time.sleep(1)

    except Exception as e:

        print("\nERROR:")
        print(e)

    # ========================================================
    # NEXT CHUNK
    # ========================================================

    current_start = current_end

# ============================================================
# COMBINE ALL CHUNKS
# ============================================================

print("\n======================================")
print("Combining all chunks...")
print("======================================")

final_df = pd.concat(
    all_dataframes,
    ignore_index=True
)

# ============================================================
# REMOVE DUPLICATES
# ============================================================

final_df.drop_duplicates(
    subset=['Datetime'],
    inplace=True
)

# ============================================================
# SORT FINAL DATA
# ============================================================

final_df.sort_values(
    by='Datetime',
    inplace=True
)

# ============================================================
# RESET INDEX
# ============================================================

final_df.reset_index(
    drop=True,
    inplace=True
)

# ============================================================
# SAVE TO CSV
# ============================================================

csv_filename = "NIFTY50_5MIN_1YEAR.csv"

final_df.to_csv(
    csv_filename,
    index=False
)

# ============================================================
# FINAL OUTPUT
# ============================================================

print("\n======================================")
print("DOWNLOAD COMPLETED")
print("======================================")

print("\nTotal Rows:", len(final_df))

print("\nCSV Saved As:")
print(csv_filename)

print("\nPreview:\n")

print(final_df.head())

print("\nLast Rows:\n")

print(final_df.tail())