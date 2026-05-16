import websocket
import json
import datetime
import pandas as pd

access_token = "your_access_token"

ws_url = f"wss://api.upstox.com/v2/feed/market-data-feed?access_token={access_token}"

# Data storage
tick_buffer = []
current_minute = None

# DataFrame to store final output
df = pd.DataFrame(columns=['time','open','high','low','close','volume'])


def on_message(ws, message):
    global tick_buffer, current_minute, df

    data = json.loads(message)

    try:
        tick = data['data'][0]   # extract tick
        ltp = tick['ltp']
        volume = tick.get('volume', 0)

        now = datetime.datetime.now()
        minute = now.replace(second=0, microsecond=0)

        if current_minute is None:
            current_minute = minute

        # If new minute starts
        if minute != current_minute:
            process_minute_data(tick_buffer, current_minute)
            tick_buffer = []
            current_minute = minute

        tick_buffer.append((ltp, volume))

    except Exception as e:
        print("Error:", e)


def process_minute_data(ticks, minute):
    global df

    if not ticks:
        return

    prices = [t[0] for t in ticks]
    volumes = [t[1] for t in ticks]

    o = prices[0]
    h = max(prices)
    l = min(prices)
    c = prices[-1]
    v = max(volumes)  # cumulative volume

    # Save to DataFrame
    df.loc[len(df)] = [minute, o, h, l, c, v]

    print(f"\n📊 {minute}")
    print(f"O:{o} H:{h} L:{l} C:{c} V:{v}")

    # Save to CSV (optional)
    df.to_csv("nifty_1min_data.csv", index=False)


def on_open(ws):
    print("✅ Connected")

    subscribe_data = {
        "guid": "abc123",
        "method": "sub",
        "data": {
            "mode": "full",
            "instrumentKeys": ["NSE_INDEX|Nifty 50"]
        }
    }

    ws.send(json.dumps(subscribe_data))


def on_error(ws, error):
    print("❌ Error:", error)


def on_close(ws):
    print("🔌 Closed")


ws = websocket.WebSocketApp(ws_url,
                            on_open=on_open,
                            on_message=on_message,
                            on_error=on_error,
                            on_close=on_close)

ws.run_forever()