# ==========================================================
# LIVE NIFTY 50 PREDICTION USING UPSTOX + LSTM
# ==========================================================
# This code:
# 1. Fetches real-time NIFTY 50 candle data minute-by-minute
# 2. Uses trained LSTM model
# 3. Predicts NEXT minute OPEN and CLOSE
# 4. Plots Actual vs Predicted prices live
# ==========================================================

import requests
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt

from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model

# ==========================================================
# LOAD TRAINED MODEL
# ==========================================================

model = load_model("lstm_live_stock_model.keras", compile=False)

# ==========================================================
# ACCESS TOKEN + INSTRUMENT KEY
# ==========================================================

ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI3NkI0VEYiLCJqdGkiOiI2YTBlOWFkNWVlMjE3ZDc1NjJiMzZkM2QiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzc5MzQyMDM3LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3Nzk0MDA4MDB9.1u3rRD9OUMlTag58WituWc-xMky76PE8XI4y0oVBVis"

INSTRUMENT_KEY = "NSE_INDEX|Nifty 50"

# ==========================================================
# API DETAILS
# ==========================================================

url = "https://api.upstox.com/v2/market-quote/quotes"

headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

# ==========================================================
# STORAGE DATAFRAME
# ==========================================================

columns = ['Open', 'High', 'Low', 'Close', 'Volume']

live_df = pd.DataFrame(columns=columns)

# ==========================================================
# SCALER
# ==========================================================

scaler = MinMaxScaler()

# ==========================================================
# PLOT STORAGE
# ==========================================================

timestamps = []

actual_open_prices = []
predicted_open_prices = []

actual_close_prices = []
predicted_close_prices = []

# ==========================================================
# LIVE GRAPH SETUP
# ==========================================================

plt.ion()

fig, ax = plt.subplots(figsize=(14,7))

# ==========================================================
# FETCH LIVE DATA FUNCTION
# ==========================================================

def fetch_live_data():

    params = {
        "instrument_key": INSTRUMENT_KEY
    }

    response = requests.get(
        url,
        headers=headers,
        params=params
    )

    data = response.json()

    nifty_data = data['data'][INSTRUMENT_KEY]

    ohlc = nifty_data['ohlc']

    open_price = ohlc['open']
    high_price = ohlc['high']
    low_price = ohlc['low']

    # Using last traded price as close approximation
    close_price = nifty_data['last_price']

    # Volume may not exist in index quote API
    volume = 0

    return {
        "Open": open_price,
        "High": high_price,
        "Low": low_price,
        "Close": close_price,
        "Volume": volume
    }

# ==========================================================
# LIVE PREDICTION LOOP
# ==========================================================

window = 60

print("Starting live prediction...\n")

for minute in range(5):

    try:

        # ==========================================
        # FETCH LIVE CANDLE
        # ==========================================

        candle = fetch_live_data()

        print(f"\nMinute {minute+1}")

        print(candle)

        # ==========================================
        # APPEND TO DATAFRAME
        # ==========================================

        new_row = pd.DataFrame([candle])

        live_df = pd.concat(
            [live_df, new_row],
            ignore_index=True
        )

        # Keep only latest 100 rows
        live_df = live_df.tail(100)

        # ==========================================
        # WAIT UNTIL WE HAVE ENOUGH DATA
        # ==========================================

        if len(live_df) < window:

            print(f"Collecting data... {len(live_df)}/{window}")

            time.sleep(60)

            continue

        # ==========================================
        # SCALE DATA
        # ==========================================

        scaled_data = scaler.fit_transform(live_df)

        # ==========================================
        # CREATE INPUT SEQUENCE
        # ==========================================

        last_60 = scaled_data[-window:]

        X_live = np.reshape(
            last_60,
            (1, window, 5)
        )

        # ==========================================
        # PREDICT NEXT OPEN + CLOSE
        # ==========================================

        prediction = model.predict(X_live, verbose=0)

        pred_open_scaled = prediction[0][0]
        pred_close_scaled = prediction[0][1]

        # ==========================================
        # INVERSE SCALE OPEN
        # ==========================================

        dummy_open = np.zeros((1,5))
        dummy_open[:,0] = pred_open_scaled

        pred_open = scaler.inverse_transform(dummy_open)[0,0]

        # ==========================================
        # INVERSE SCALE CLOSE
        # ==========================================

        dummy_close = np.zeros((1,5))
        dummy_close[:,3] = pred_close_scaled

        pred_close = scaler.inverse_transform(dummy_close)[0,3]

        # ==========================================
        # ACTUAL VALUES
        # ==========================================

        actual_open = candle['Open']
        actual_close = candle['Close']

        current_time = datetime.now().strftime("%H:%M:%S")

        # ==========================================
        # STORE VALUES
        # ==========================================

        timestamps.append(current_time)

        actual_open_prices.append(actual_open)
        predicted_open_prices.append(pred_open)

        actual_close_prices.append(actual_close)
        predicted_close_prices.append(pred_close)

        # ==========================================
        # PRINT PREDICTION
        # ==========================================

        print("\nActual Open :", actual_open)
        print("Pred Open   :", pred_open)

        print("\nActual Close:", actual_close)
        print("Pred Close  :", pred_close)

        # ==========================================
        # LIVE GRAPH
        # ==========================================

        ax.clear()

        # OPEN PRICE GRAPH
        ax.plot(
            timestamps,
            actual_open_prices,
            marker='o',
            label='Actual Open'
        )

        ax.plot(
            timestamps,
            predicted_open_prices,
            marker='o',
            linestyle='--',
            label='Predicted Open'
        )

        # CLOSE PRICE GRAPH
        ax.plot(
            timestamps,
            actual_close_prices,
            marker='o',
            label='Actual Close'
        )

        ax.plot(
            timestamps,
            predicted_close_prices,
            marker='o',
            linestyle='--',
            label='Predicted Close'
        )

        ax.set_title(
            "NIFTY 50 Live Prediction"
        )

        ax.set_xlabel("Time")
        ax.set_ylabel("Price")

        ax.legend()

        plt.xticks(rotation=45)

        plt.tight_layout()

        plt.pause(1)

        # ==========================================
        # WAIT 1 MINUTE
        # ==========================================

        if minute < 4:

            print("\nWaiting for next minute candle...\n")

            time.sleep(60)

    except Exception as e:

        print("\nERROR OCCURRED:\n")
        print(e)

        break

# ==========================================================
# FINAL GRAPH
# ==========================================================

plt.ioff()
plt.show()

print("\nLive prediction completed.")