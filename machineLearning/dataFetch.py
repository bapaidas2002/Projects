import websocket
import json
import datetime
import pandas as pd

# NOTE: Replace with a valid token from https://upstox.com/.
# An expired or invalid token will return a WebSocket 401 Unauthorized handshake error.
access_token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI3NkI0VEYiLCJqdGkiOiI2YTA5OWJjNTY5YjlkYzU5MDk1ODg1Y2MiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzc5MDE0NTk3LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NzkwNTUyMDB9.dO96bl3AtXlaKduwHj-sCLqwisMFI-bmgBBYSavsVy0"

ws_url = f"wss://api.upstox.com/v2/feed/market-data-feed?access_token={access_token}"
print(f"Connecting to WebSocket: {ws_url}")
print("="*50)

# Live candle state
current_minute = None
current_bar = {
    "time": None,
    "open": None,
    "high": None,
    "low": None,
    "close": None,
    "volume": 0,
}

# DataFrame to store finished 1-minute candles
df = pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])


def parse_tick_time(tick: dict) -> datetime.datetime:
    for key in ("timestamp", "time", "lastTradedTime", "ltpTime", "tradeTime"):
        value = tick.get(key)
        if not value:
            continue
        if isinstance(value, int):
            return datetime.datetime.fromtimestamp(value / 1000)
        if isinstance(value, str):
            try:
                return datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                continue
    return datetime.datetime.now()


def reset_bar(minute: datetime.datetime) -> None:
    global current_bar
    current_bar = {
        "time": minute,
        "open": None,
        "high": None,
        "low": None,
        "close": None,
        "volume": 0,
    }


def update_bar(price: float, volume: float) -> None:
    global current_bar
    if current_bar["open"] is None:
        current_bar["open"] = price
        current_bar["high"] = price
        current_bar["low"] = price
        current_bar["close"] = price
        current_bar["volume"] = volume
    else:
        current_bar["high"] = max(current_bar["high"], price)
        current_bar["low"] = min(current_bar["low"], price)
        current_bar["close"] = price
        current_bar["volume"] = max(current_bar["volume"], volume)


def print_live_bar() -> None:
    if current_bar["open"] is None:
        return
    print(
        f"⏱️  Live {current_bar['time']} | "
        f"O:{current_bar['open']} H:{current_bar['high']} "
        f"L:{current_bar['low']} C:{current_bar['close']} V:{current_bar['volume']}"
    )


def finalize_bar() -> None:
    global df
    if current_bar["open"] is None:
        return

    df.loc[len(df)] = [
        current_bar["time"],
        current_bar["open"],
        current_bar["high"],
        current_bar["low"],
        current_bar["close"],
        current_bar["volume"],
    ]
    df.to_csv(OUTPUT_CSV, index=False)
    print(
        f"\n✅ Finalized minute {current_bar['time']} | "
        f"O:{current_bar['open']} H:{current_bar['high']} "
        f"L:{current_bar['low']} C:{current_bar['close']} V:{current_bar['volume']}"
    )


def on_message(ws, message):
    global current_minute

    data = json.loads(message)
    if not isinstance(data, dict) or "data" not in data:
        return

    try:
        tick = data["data"][0]
        price = tick.get("ltp")
        volume = tick.get("volume", 0)
        tick_time = parse_tick_time(tick)

        minute = tick_time.replace(second=0, microsecond=0)

        if current_minute is None:
            current_minute = minute
            reset_bar(current_minute)
            print(f"📍 First live tick for {INSTRUMENT_KEY} at {tick_time}")

        if minute != current_minute:
            finalize_bar()
            current_minute = minute
            reset_bar(current_minute)

        if price is None:
            return

        update_bar(price, volume)
        print_live_bar()

    except KeyError as e:
        print(f"⚠️  KeyError: {e} - Data format may differ: {message[:120]}")
    except Exception as e:
        print(f"❌ Error processing tick: {e}")


def on_open(ws):
    print("✅ WebSocket Connected Successfully!")
    print("📤 Sending subscription request...")

    subscribe_data = {
        "guid": "abc123",
        "method": "sub",
        "data": {
            "mode": "full",
            "instrumentKeys": [INSTRUMENT_KEY]
        }
    }

    ws.send(json.dumps(subscribe_data))
    print("✅ Subscription request sent. Waiting for data...")


def on_error(ws, error):
    print("❌ Error:", error)


def on_close(ws, close_status_code, close_msg):
    print("🔌 Connection Closed")
    print(f"Close status: {close_status_code}, message: {close_msg}")
    if current_minute is not None:
        print("\n⚠️ Processing remaining minute data before closing...")
        finalize_bar()
    print(f"\n✅ Final DataFrame saved with {len(df)} records")
    print(df)


ws = websocket.WebSocketApp(ws_url,
                            on_open=on_open,
                            on_message=on_message,
                            on_error=on_error,
                            on_close=on_close)

print("\n🔄 Starting WebSocket connection...")
try:
    ws.run_forever()
except KeyboardInterrupt:
    print("\n⏹️  Interrupted by user")
except Exception as e:
    print(f"\n❌ Fatal Error: {e}")